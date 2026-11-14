import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import workerModule from "./worker.js";

const worker = await readFile(new URL("./worker.js", import.meta.url), "utf8");
const schema = await readFile(new URL("./schema.sql", import.meta.url), "utf8");

test("webhook is guarded by the configured Telegram secret", () => {
  assert.match(worker, /X-Telegram-Bot-Api-Secret-Token/);
  assert.match(worker, /env\.WEBHOOK_SECRET/);
});

test("content wizard accepts Telegram documents and photos", () => {
  assert.match(worker, /m\.document\.file_id/);
  assert.match(worker, /m\.photo\[m\.photo\.length-1\]\.file_id/);
  assert.match(worker, /step==="file"/);
  assert.match(worker, /step==="image"/);
});

test("catalog delivers stored images and documents through Telegram", () => {
  assert.match(worker, /"sendPhoto"/);
  assert.match(worker, /"sendDocument"/);
  assert.match(worker, /item\.image_file_id/);
  assert.match(worker, /item\.file_id/);
});

test("channel publishing and media-preserving broadcast are wired", () => {
  assert.match(worker, /adm:channel_post/);
  assert.match(worker, /adm:post:publish/);
  assert.match(worker, /"copyMessage"/);
});

test("channel post wizard offers and preserves all three button styles", () => {
  assert.match(worker, /adm:post:style:primary/);
  assert.match(worker, /adm:post:style:success/);
  assert.match(worker, /adm:post:style:danger/);
  assert.match(worker, /post_button_style/);
  assert.match(worker, /style:d\.post_button_style\|\|"primary"/);
});

test("D1 schema stores media metadata for content", () => {
  assert.match(schema, /file_id TEXT NOT NULL DEFAULT ''/);
  assert.match(schema, /file_name TEXT NOT NULL DEFAULT ''/);
  assert.match(schema, /image_file_id TEXT NOT NULL DEFAULT ''/);
  assert.match(schema, /UNIQUE\(category, slug\)/);
});

test("webhook requires all production bindings and a matching secret", () => {
  assert.match(worker, /!env\.BOT_TOKEN \|\| !env\.WEBHOOK_SECRET \|\| !env\.DB/);
  assert.match(worker, /X-Telegram-Bot-Api-Secret-Token/);
  assert.match(worker, /status:401/);
});

test("webhook deduplicates updates and asks Telegram to retry processing failures", () => {
  assert.match(schema, /CREATE TABLE IF NOT EXISTS processed_updates/);
  assert.match(worker, /claimUpdate\(env,update\.update_id\)/);
  assert.match(worker, /status='processed'/);
  assert.match(worker, /status='failed'/);
  assert.match(worker, /status:503/);
});

test("health endpoint checks the persistent D1 binding", () => {
  assert.match(worker, /url\.pathname==="\/healthz"/);
  assert.match(worker, /SELECT 1 AS ok/);
});


test("health endpoint reports D1 readiness without exposing configuration", async () => {
  const response = await workerModule.fetch(
    new Request("https://worker.example/healthz"),
    { DB: { prepare: () => ({ first: async () => ({ ok: 1 }) }) } },
  );
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { status: "ok", database: "ok" });
});

test("health endpoint fails closed when D1 is unavailable", async () => {
  const response = await workerModule.fetch(
    new Request("https://worker.example/healthz"),
    { DB: { prepare: () => ({ first: async () => { throw new Error("offline"); } }) } },
  );
  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), { status: "error", database: "unavailable" });
});

test("webhook rejects missing production configuration and invalid secrets", async () => {
  const noConfig = await workerModule.fetch(
    new Request("https://worker.example/telegram/webhook", { method: "POST", body: "{}" }),
    {},
  );
  assert.equal(noConfig.status, 503);

  const unauthorized = await workerModule.fetch(
    new Request("https://worker.example/telegram/webhook", {
      method: "POST",
      headers: { "content-type": "application/json", "X-Telegram-Bot-Api-Secret-Token": "wrong" },
      body: JSON.stringify({ update_id: 1 }),
    }),
    { BOT_TOKEN: "test", WEBHOOK_SECRET: "correct", DB: {} },
  );
  assert.equal(unauthorized.status, 401);
});

test("webhook acknowledges a duplicate update without processing it twice", async () => {
  const response = await workerModule.fetch(
    new Request("https://worker.example/telegram/webhook", {
      method: "POST",
      headers: { "content-type": "application/json", "X-Telegram-Bot-Api-Secret-Token": "secret" },
      body: JSON.stringify({ update_id: 42 }),
    }),
    {
      BOT_TOKEN: "test",
      WEBHOOK_SECRET: "secret",
      DB: { prepare: () => ({ bind: () => ({ first: async () => null }) }) },
    },
  );
  assert.equal(response.status, 200);
  assert.equal(await response.text(), "Duplicate update");
});


function makeD1({users=[], states=[], content=[]}={}) {
  const userRows=new Map(users.map(row=>[String(row.user_id),{...row}]));
  const stateRows=new Map(states.map(row=>[String(row.user_id),{...row}]));
  const contentRows=new Map(content.map(row=>[row.category+":"+row.slug,{...row}]));
  const processed=new Map();

  return {
    userRows,stateRows,contentRows,processed,
    prepare(sql) {
      const query=sql.replace(/\s+/g," ").trim().toLowerCase();
      let values=[];
      const statement={
        bind(...args) { values=args; return statement; },
        async run() {
          if(query.startsWith("insert into users")) {
            const [id,username,firstName]=values;
            const key=String(id);
            const existing=userRows.get(key);
            if(existing) {
              existing.username=username||"";
              existing.first_name=firstName||"";
              existing.last_seen_at="now";
            } else {
              userRows.set(key,{user_id:id,username:username||"",first_name:firstName||"",language:"",created_at:"now",last_seen_at:"now"});
            }
          } else if(query.startsWith("update users set language")) {
            const [language,id]=values;
            const row=userRows.get(String(id));
            if(row) row.language=language;
          } else if(query.startsWith("insert into user_state")) {
            const [id,step,data]=values;
            stateRows.set(String(id),{user_id:id,step,data,updated_at:"now"});
          } else if(query.startsWith("delete from user_state")) {
            stateRows.delete(String(values[0]));
          } else if(query.startsWith("update processed_updates")) {
            const status=(query.match(/set status='([^']+)'/)||[])[1]||"processed";
            const row=processed.get(String(values[0]));
            if(row) row.status=status;
          }
          return {success:true};
        },
        async first() {
          if(query.startsWith("insert into processed_updates")) {
            const id=String(values[0]);
            const existing=processed.get(id);
            if(existing && existing.status!=="failed") return null;
            processed.set(id,{status:"processing"});
            return {update_id:Number(id)};
          }
          if(query.startsWith("select * from users where user_id")) {
            const row=userRows.get(String(values[0]));
            return row?{...row}:null;
          }
          if(query.startsWith("select * from user_state where user_id")) {
            const row=stateRows.get(String(values[0]));
            return row?{...row}:null;
          }
          if(query.startsWith("select * from content_items where category")) {
            const row=contentRows.get(values[0]+":"+values[1]);
            return row?{...row}:null;
          }
          if(query.startsWith("select count(*)")) return {n:0};
          return null;
        },
        async all() {
          if(query.startsWith("select user_id from users")) {
            return {results:Array.from(userRows.values()).map(row=>({user_id:row.user_id}))};
          }
          return {results:[]};
        }
      };
      return statement;
    }
  };
}

function mockTelegram(t,{fileContent="print('test')" }={}) {
  const originalFetch=globalThis.fetch;
  const calls=[];
  globalThis.fetch=async (input,init={})=>{
    const url=String(input);
    if(url.startsWith("https://api.telegram.org/file/")) {
      calls.push({method:"downloadFile",url});
      return new Response(fileContent,{status:200});
    }
    const method=url.slice(url.lastIndexOf("/")+1);
    const body=init.body?JSON.parse(init.body):{};
    calls.push({method,body});
    let result={ok:true,result:{}};
    if(method==="getChatMember") result={ok:true,result:{status:"member"}};
    if(method==="getFile") result={ok:true,result:{file_path:"documents/payload.lua",file_size:fileContent.length}};
    return new Response(JSON.stringify(result),{status:200,headers:{"content-type":"application/json"}});
  };
  t.after(()=>{globalThis.fetch=originalFetch;});
  return calls;
}

async function postUpdate(env,update) {
  return workerModule.fetch(
    new Request("https://worker.example/telegram/webhook",{
      method:"POST",
      headers:{"content-type":"application/json","X-Telegram-Bot-Api-Secret-Token":env.WEBHOOK_SECRET},
      body:JSON.stringify(update)
    }),
    env
  );
}

function testEnv(DB,adminIds="") {
  return {
    BOT_TOKEN:"test-token",
    WEBHOOK_SECRET:"test-webhook-secret",
    ADMIN_IDS:adminIds,
    CHANNEL_ID:"@private-test-channel",
    CHANNEL_URL:"https://t.me/private-test-channel",
    DB
  };
}

test("home menu uses the same persistent reply-keyboard layout as the Python bot", async (t) => {
  const calls=mockTelegram(t);
  const DB=makeD1({users:[{user_id:101,language:"ru"}]});
  const env=testEnv(DB);
  const response=await postUpdate(env,{
    update_id:101,
    message:{message_id:1,from:{id:101,first_name:"Test"},chat:{id:101,type:"private"},text:"/start"}
  });
  assert.equal(response.status,200);
  const sent=calls.filter(call=>call.method==="sendMessage").at(-1);
  assert.ok(sent.body.reply_markup.keyboard);
  assert.equal(sent.body.reply_markup.resize_keyboard,true);
  assert.equal(sent.body.reply_markup.keyboard.length,3);
  assert.equal(sent.body.reply_markup.inline_keyboard,undefined);
});

test("admin command clears an unfinished content wizard", async (t) => {
  const calls=mockTelegram(t);
  const DB=makeD1({
    users:[{user_id:9001,language:"ru"}],
    states:[{user_id:9001,step:"title_ru",data:JSON.stringify({category:"scripts",slug:"mm2"})}]
  });
  const env=testEnv(DB,"9001");
  const first=await postUpdate(env,{
    update_id:201,
    message:{message_id:1,from:{id:9001,first_name:"Admin"},chat:{id:9001,type:"private"},text:"/admin"}
  });
  assert.equal(first.status,200);
  assert.equal(DB.stateRows.has("9001"),false);

  const second=await postUpdate(env,{
    update_id:202,
    message:{message_id:2,from:{id:9001,first_name:"Admin"},chat:{id:9001,type:"private"},text:"Свободное сообщение"}
  });
  assert.equal(second.status,200);
  const messages=calls.filter(call=>call.method==="sendMessage").map(call=>call.body.text);
  assert.ok(messages.includes("Выбери раздел:"));
});

test("content wizard rejects invalid URLs without advancing to file upload", async (t) => {
  const calls=mockTelegram(t);
  const DB=makeD1({
    users:[{user_id:9002,language:"ru"}],
    states:[{user_id:9002,step:"url",data:JSON.stringify({category:"scripts",slug:"mm2",title_ru:"MM2",title_en:"MM2"})}]
  });
  const env=testEnv(DB,"9002");
  const response=await postUpdate(env,{
    update_id:301,
    message:{message_id:3,from:{id:9002,first_name:"Admin"},chat:{id:9002,type:"private"},text:"javascript:alert(1)"}
  });
  assert.equal(response.status,200);
  assert.equal(DB.stateRows.get("9002").step,"url");
  assert.ok(calls.some(call=>call.method==="sendMessage"&&call.body.text==="Неверный формат. Попробуй ещё раз."));
});

test("text script files are delivered as escaped copyable code, matching Python bot behavior", async (t) => {
  const calls=mockTelegram(t,{fileContent:"print('<mm2>')\\nprint('second')"});
  const DB=makeD1({
    users:[{user_id:404,language:"ru"}],
    content:[{category:"scripts",slug:"adopt_me",title_ru:"Adopt Me",title_en:"Adopt Me",body_ru:"",body_en:"",version:"",url:"",file_id:"telegram-file-id",file_name:"script.lua",image_file_id:""}]
  });
  const env=testEnv(DB);
  const response=await postUpdate(env,{
    update_id:401,
    callback_query:{id:"callback-1",from:{id:404,first_name:"Test"},data:"item:scripts:adopt_me",message:{message_id:9,chat:{id:404,type:"private"}}}
  });
  assert.equal(response.status,200);
  assert.ok(calls.some(call=>call.method==="downloadFile"));
  assert.ok(calls.some(call=>call.method==="sendMessage"&&call.body.text.includes("<pre><code>print('&lt;mm2&gt;')")));
  assert.equal(calls.some(call=>call.method==="sendDocument"),false);
});
