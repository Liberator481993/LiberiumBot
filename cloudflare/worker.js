const API = (token) => `https://api.telegram.org/bot${token}/`;

const CATALOGS = {
  scripts: [["mm2", "Murder Mystery 2"], ["adopt_me", "Adopt Me"], ["blade_ball", "Blade Ball"]],
  injectors: [["delta", "Delta"], ["arceus_x", "Arceus X — Recommended 🔥"]],
  guides: [["install", "Установка / Installation"], ["launch", "Запуск / Launch"], ["troubleshooting", "Решение проблем / Troubleshooting"]],
};

const T = {
  ru: {
    choose_language:"🌐 Выбери язык интерфейса:", welcome:"✨ <b>Добро пожаловать в Liberium Bot!</b>\n\nЗдесь собраны скрипты, инжекторы и полезные инструкции экосистемы Liberium.",
    subscribe:"🔒 <b>Для доступа к боту нужна подписка на канал.</b>\nПодпишись и нажми «Проверить подписку».", check:"✅ Проверить подписку", channel:"📢 Открыть канал", not_sub:"Подписка пока не найдена. Сначала подпишись на канал.", subscribed:"✅ Подписка подтверждена!",
    scripts:"🎮 Скрипты", injectors:"📲 Инжекторы", guides:"📚 Гайды", profile:"👤 Профиль", language:"🌐 Язык", admin:"🛠 Админ-панель", choose:"Выбери раздел:", choose_item:"Выбери нужный материал:", not_published:"Этот материал пока не опубликован. Загляни позже.", version:"Версия", download:"📥 Скачать / открыть", back:"⬅️ Назад",
    admin_title:"🛠 <b>Панель управления Liberium</b>", content:"🗂 Управление материалами", broadcast:"📣 Рассылка", stats:"📊 Статистика", denied:"⛔ У тебя нет доступа к админ-панели.", cat:"Выбери раздел для управления:", item:"Выбери материал. Его можно обновить или удалить:", edit:"✏️ Добавить / обновить", del:"🗑 Удалить", deleted:"Материал удалён.", title_ru:"Отправь название на русском:", title_en:"Отправь название на английском:", body_ru:"Отправь описание на русском:", body_en:"Отправь описание на английском:", version_q:"Укажи версию или отправь «-», если версии нет:", url:"Отправь ссылку (https://...) или «-», если ссылки нет:", file:"Отправь документ файлом или «-», чтобы пропустить:", saved:"✅ Материал успешно сохранён.", invalid:"Неверный формат. Попробуй ещё раз.", broadcast_q:"Отправь текст для рассылки:", broadcast_done:"Рассылка завершена. Доставлено: {sent}, ошибок: {failed}.", stats_text:"📊 <b>Статистика</b>\nПользователей: {users}\nМатериалов: {content}", support:"По вопросам и предложениям напиши администрации канала @mm2hubscripts.", language_saved:"Язык сохранён."
  },
  en: {
    choose_language:"🌐 Choose your interface language:", welcome:"✨ <b>Welcome to Liberium Bot!</b>\n\nFind scripts, injectors and useful guides from the Liberium ecosystem.",
    subscribe:"🔒 <b>Channel subscription is required.</b>\nSubscribe to the channel, then tap “Check subscription”.", check:"✅ Check subscription", channel:"📢 Open channel", not_sub:"Subscription not found. Please join the channel first.", subscribed:"✅ Subscription confirmed!",
    scripts:"🎮 Scripts", injectors:"📲 Injectors", guides:"📚 Guides", profile:"👤 Profile", language:"🌐 Language", admin:"🛠 Admin panel", choose:"Choose a section:", choose_item:"Choose an item:", not_published:"This item has not been published yet. Check back later.", version:"Version", download:"📥 Download / open", back:"⬅️ Back",
    admin_title:"🛠 <b>Liberium control panel</b>", content:"🗂 Manage content", broadcast:"📣 Broadcast", stats:"📊 Statistics", denied:"⛔ You do not have access to the admin panel.", cat:"Choose a section to manage:", item:"Choose an item to update or delete:", edit:"✏️ Add / update", del:"🗑 Delete", deleted:"Content deleted.", title_ru:"Send the Russian title:", title_en:"Send the English title:", body_ru:"Send the Russian description:", body_en:"Send the English description:", version_q:"Send the version, or “-” if not applicable:", url:"Send a URL (https://...) or “-” if there is no link:", file:"Send the document file, or “-” to skip:", saved:"✅ Content saved successfully.", invalid:"Invalid format. Try again.", broadcast_q:"Send the text to broadcast:", broadcast_done:"Broadcast finished. Delivered: {sent}, failed: {failed}.", stats_text:"📊 <b>Statistics</b>\nUsers: {users}\nContent items: {content}", support:"For help and suggestions, contact @mm2hubscripts.", language_saved:"Language saved."
  }
};
const tr = (l,k) => (T[l] || T.ru)[k] || T.ru[k] || k;
const kb = (rows) => ({inline_keyboard:rows});
const btn = (text, callback_data) => ({text, callback_data});
const esc = (s="") => String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");

async function tg(env, method, body) {
  const r = await fetch(API(env.BOT_TOKEN)+method,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(body)});
  const data=await r.json();
  if(!data.ok) console.error("Telegram API",method,data.description);
  return data;
}
async function send(env, chat_id, text, extra={}) {
  return tg(env,"sendMessage",{chat_id,text,parse_mode:"HTML",...extra});
}
async function copyBroadcast(env, sourceChat, sourceMessage, targetChat) {
  return tg(env,"copyMessage",{chat_id:targetChat,from_chat_id:sourceChat,message_id:sourceMessage});
}
async function user(env,id,from={}) {
  await env.DB.prepare("INSERT INTO users(user_id,username,first_name,language,created_at,last_seen_at) VALUES(?,?,?,'',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP) ON CONFLICT(user_id) DO UPDATE SET username=excluded.username,first_name=excluded.first_name,last_seen_at=CURRENT_TIMESTAMP")
    .bind(id,from.username||"",from.first_name||"").run();
  return await env.DB.prepare("SELECT * FROM users WHERE user_id=?").bind(id).first();
}
async function subscribed(env,id) {
  const r=await tg(env,"getChatMember",{chat_id:env.CHANNEL_ID||"@mm2hubscripts",user_id:id});
  return !!(r.ok && ["member","administrator","creator"].includes(r.result.status));
}
const admins=(env)=>new Set(String(env.ADMIN_IDS||"").split(",").map(x=>x.trim()).filter(Boolean));
async function home(env,chat,id,lang) {
  const rows=[[{text:tr(lang,"scripts"),callback_data:"cat:scripts"},{text:tr(lang,"injectors"),callback_data:"cat:injectors"}],[{text:tr(lang,"guides"),callback_data:"cat:guides"},{text:tr(lang,"profile"),callback_data:"profile"}],[{text:tr(lang,"language"),callback_data:"language"}]];
  if(admins(env).has(String(id))) rows.push([btn(tr(lang,"admin"),"adm:home")]);
  await send(env,chat,tr(lang,"welcome"),{reply_markup:kb(rows)});
}
async function access(env,chat,id,lang) {
  if(await subscribed(env,id)) return true;
  await send(env,chat,tr(lang,"subscribe"),{reply_markup:kb([[{text:tr(lang,"channel"),url:env.CHANNEL_URL||"https://t.me/mm2hubscripts"}],[btn(tr(lang,"check"),"sub:check")]])});
  return false;
}
async function state(env,id) { return env.DB.prepare("SELECT * FROM user_state WHERE user_id=?").bind(id).first(); }
async function setState(env,id,step,data={}) {
  await env.DB.prepare("INSERT INTO user_state(user_id,step,data,updated_at) VALUES(?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(user_id) DO UPDATE SET step=excluded.step,data=excluded.data,updated_at=CURRENT_TIMESTAMP").bind(id,step,JSON.stringify(data)).run();
}
async function clearState(env,id) { await env.DB.prepare("DELETE FROM user_state WHERE user_id=?").bind(id).run(); }
async function handleMessage(env,m) {
  if(!m.from || !m.chat) return;
  const id=m.from.id, chat=m.chat.id, u=await user(env,id,m.from), lang=u.language||"ru";
  const text=m.text||"";
  if(text.startsWith("/start")) {
    if(!u.language) return send(env,chat,tr("ru","choose_language"),{reply_markup:kb([[btn("🇷🇺 Русский","lang:ru"),btn("🇬🇧 English","lang:en")]])});
    if(await access(env,chat,id,lang)) return home(env,chat,id,lang);
    return;
  }
  if(text==="/help") return send(env,chat,tr(lang,"support"));
  if(text==="/cancel") { await clearState(env,id); return send(env,chat,lang==="ru"?"Действие отменено.":"Action cancelled."); }
  if(text==="/admin" && admins(env).has(String(id))) {
    if(!(await access(env,chat,id,lang))) return;
    return send(env,chat,tr(lang,"admin_title"),{reply_markup:kb([[btn(lang==="ru"?"📢 Создать пост в канал":"📢 Create channel post","adm:channel_post")],[btn(tr(lang,"content"),"adm:content")],[btn(tr(lang,"broadcast"),"adm:broadcast")],[btn(tr(lang,"stats"),"adm:stats")],[btn(tr(lang,"back"),"nav:home")]])});
  }
  const st=await state(env,id);
  if(st && admins(env).has(String(id)) && (text || m.document || m.photo)) {
    let d={}; try{d=JSON.parse(st.data||"{}")}catch{}
    const step=st.step;
    const prompts={title_ru:"title_en",title_en:"body_ru",body_ru:"body_en",body_en:"version",version:"url",url:"file"};
    if(step==="broadcast") {
      const users=await env.DB.prepare("SELECT user_id FROM users").all(); let sent=0,failed=0;
      for(const row of users.results||[]) {
        const r=await copyBroadcast(env,chat,m.message_id,row.user_id);
        if(r.ok) sent++; else failed++;
        if(r.error_code===429) await new Promise(resolve=>setTimeout(resolve,Math.max(1000,(r.parameters?.retry_after||1)*1000)));
        else await new Promise(resolve=>setTimeout(resolve,40));
      }
      await clearState(env,id); return send(env,chat,tr(lang,"broadcast_done").replace("{sent}",sent).replace("{failed}",failed));
    }
    if(step==="file") {
      if(m.document) { d.file_id=m.document.file_id; d.file_name=m.document.file_name||"download"; }
      else if(text==="/skip"||text==="-") { d.file_id=""; d.file_name=""; }
      else return send(env,chat,lang==="ru"?"Отправь документ или /skip.":"Send a document or /skip.");
      await setState(env,id,"image",d);
      return send(env,chat,lang==="ru"?"Теперь отправь изображение как фото или /skip.":"Now send an image as a photo or /skip.");
    }
    if(step==="image") {
      if(m.photo?.length) d.image_file_id=m.photo[m.photo.length-1].file_id;
      else if(text==="/skip"||text==="-") d.image_file_id="";
      else return send(env,chat,lang==="ru"?"Отправь фото или /skip.":"Send a photo or /skip.");
      await env.DB.prepare("INSERT INTO content_items(category,slug,title_ru,title_en,body_ru,body_en,version,url,file_id,file_name,image_file_id,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(category,slug) DO UPDATE SET title_ru=excluded.title_ru,title_en=excluded.title_en,body_ru=excluded.body_ru,body_en=excluded.body_en,version=excluded.version,url=excluded.url,file_id=excluded.file_id,file_name=excluded.file_name,image_file_id=excluded.image_file_id,updated_at=CURRENT_TIMESTAMP")
        .bind(d.category,d.slug,d.title_ru,d.title_en,d.body_ru,d.body_en,d.version==="-"?"":d.version,d.url==="-"?"":d.url,d.file_id||"",d.file_name||"",d.image_file_id||"").run();
      await clearState(env,id); return send(env,chat,tr(lang,"saved"));
    }
    if(step==="post_text") {
      if(!text.trim()) return send(env,chat,lang==="ru"?"Отправь текст поста.":"Send the post text.");
      d.post_text=text.trim(); await setState(env,id,"post_photo",d);
      return send(env,chat,lang==="ru"?"Отправь фото или /skip.":"Send a photo or /skip.");
    }
    if(step==="post_photo") {
      if(m.photo?.length) d.post_photo_id=m.photo[m.photo.length-1].file_id;
      else if(text==="/skip"||text==="-") d.post_photo_id="";
      else return send(env,chat,lang==="ru"?"Отправь фото или /skip.":"Send a photo or /skip.");
      if(d.post_photo_id && d.post_text.length>1024) return send(env,chat,lang==="ru"?"Подпись к фото не должна превышать 1024 символа.":"Photo caption must not exceed 1024 characters.");
      await setState(env,id,"post_button",d);
      return send(env,chat,lang==="ru"?"Напиши текст кнопки (до 64 символов):":"Send the button label (up to 64 characters).");
    }
    if(step==="post_button") {
      if(!text.trim()||text.trim().length>64) return send(env,chat,lang==="ru"?"Текст кнопки должен быть от 1 до 64 символов.":"Button label must be 1–64 characters.");
      d.post_button=text.trim(); await setState(env,id,"post_style",d);
      return send(env,chat,lang==="ru"?"Выбери цвет кнопки:":"Choose the button colour:",{reply_markup:kb([
        [{text:lang==="ru"?"🔵 Синий":"🔵 Blue",callback_data:"adm:post:style:primary",style:"primary"}],
        [{text:lang==="ru"?"🟢 Зелёный":"🟢 Green",callback_data:"adm:post:style:success",style:"success"}],
        [{text:lang==="ru"?"🔴 Красный":"🔴 Red",callback_data:"adm:post:style:danger",style:"danger"}]
      ])});
    }
    if(step==="title_ru"||step==="title_en"||step==="body_ru"||step==="body_en"||step==="version"||step==="url"||step==="file") {
      const key=step; d[key]=text==="/"?"":text;
      const next=prompts[step];
      if(next) { await setState(env,id,next,d); return send(env,chat,tr(lang,next==="version"?"version_q":next==="url"?"url":next==="file"?"file":next)); }
      if(!["-",""].includes(d.url) && !/^https?:\/\//i.test(d.url)) return send(env,chat,tr(lang,"invalid"));
      await env.DB.prepare("INSERT INTO content_items(category,slug,title_ru,title_en,body_ru,body_en,version,url,file_id,updated_at) VALUES(?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(category,slug) DO UPDATE SET title_ru=excluded.title_ru,title_en=excluded.title_en,body_ru=excluded.body_ru,body_en=excluded.body_en,version=excluded.version,url=excluded.url,file_id=excluded.file_id,updated_at=CURRENT_TIMESTAMP")
        .bind(d.category,d.slug,d.title_ru,d.title_en,d.body_ru,d.body_en,d.version==="-"?"":d.version,d.url==="-"?"":d.url,d.file_id==="-"?"":d.file_id).run();
      await clearState(env,id); return send(env,chat,tr(lang,"saved"));
    }
  }
  if(!(await access(env,chat,id,lang))) return;
  const labels={ [tr(lang,"scripts")]:"scripts",[tr(lang,"injectors")]:"injectors",[tr(lang,"guides")]:"guides",[tr(lang,"profile")]:"profile",[tr(lang,"language")]:"language",[tr(lang,"admin")]:"admin" };
  const action=labels[text];
  if(action==="scripts"||action==="injectors"||action==="guides") return send(env,chat,tr(lang,"choose_item"),{reply_markup:catalogMarkup(action,lang)});
  if(action==="profile") return send(env,chat,`👤 <b>${lang==="ru"?"Твой профиль":"Your profile"}</b>\nID: <code>${id}</code>\nLanguage: ${lang}`);
  if(action==="language") return send(env,chat,tr(lang,"choose_language"),{reply_markup:kb([[btn("🇷🇺 Русский","lang:ru"),btn("🇬🇧 English","lang:en")]])});
  if(action==="admin"&&admins(env).has(String(id))) return send(env,chat,tr(lang,"admin_title"),{reply_markup:kb([[btn(lang==="ru"?"📢 Создать пост в канал":"📢 Create channel post","adm:channel_post")],[btn(tr(lang,"content"),"adm:content")],[btn(tr(lang,"broadcast"),"adm:broadcast")],[btn(tr(lang,"stats"),"adm:stats")]])});
  return send(env,chat,tr(lang,"choose"));
}
function catalogMarkup(category,lang) {
  const rows=CATALOGS[category].map(([slug,title])=>[btn(category==="injectors"&&slug==="arceus_x"?(lang==="ru"?"Arceus X — Рекомендуется 🔥":title):title,`item:${category}:${slug}`)]);
  rows.push([btn(tr(lang,"back"),"nav:home")]); return kb(rows);
}
async function handleCallback(env,c) {
  const id=c.from.id, chat=c.message?.chat?.id, msgid=c.message?.message_id;
  const u=await user(env,id,c.from), lang=u.language||"ru", data=c.data||"";
  await tg(env,"answerCallbackQuery",{callback_query_id:c.id});
  if(data.startsWith("lang:")) {
    const l=data.split(":")[1]; if(!["ru","en"].includes(l))return;
    await env.DB.prepare("UPDATE users SET language=? WHERE user_id=?").bind(l,id).run();
    if(await access(env,chat,id,l)) return home(env,chat,id,l);
    return;
  }
  if(data==="sub:check") { if(await subscribed(env,id)) return home(env,chat,id,lang); return send(env,chat,tr(lang,"not_sub")); }
  if(data==="language") return send(env,chat,tr(lang,"choose_language"),{reply_markup:kb([[btn("🇷🇺 Русский","lang:ru"),btn("🇬🇧 English","lang:en")]])});
  if(data==="nav:home") { if(await access(env,chat,id,lang))return home(env,chat,id,lang); return; }
  if(!(await access(env,chat,id,lang))) return;
  if(data.startsWith("cat:")) { const cat=data.split(":")[1]; if(CATALOGS[cat]) return send(env,chat,tr(lang,"choose_item"),{reply_markup:catalogMarkup(cat,lang)}); }
  if(data.startsWith("item:")) {
    const [,cat,slug]=data.split(":"); if(!CATALOGS[cat]?.some(x=>x[0]===slug))return;
    const item=await env.DB.prepare("SELECT * FROM content_items WHERE category=? AND slug=?").bind(cat,slug).first();
    if(!item)return send(env,chat,tr(lang,"not_published"));
    let text=`<b>${esc(lang==="ru"?item.title_ru:item.title_en)}</b>`;
    if(item.version)text+=`\n${tr(lang,"version")}: <code>${esc(item.version)}</code>`;
    const body=lang==="ru"?item.body_ru:item.body_en;if(body)text+=`\n\n${esc(body)}`;
    const extra={}; if(item.url)extra.reply_markup=kb([[{text:tr(lang,"download"),url:item.url}]]);
    if(item.image_file_id) {
      const photo=await tg(env,"sendPhoto",{chat_id:chat,photo:item.image_file_id,caption:text.length<=1024?text:text.slice(0,1000),parse_mode:"HTML",...extra});
      if(!photo.ok) await send(env,chat,text,extra);
    } else await send(env,chat,text,extra);
    if(cat==="scripts"&&slug==="mm2") await send(env,chat,'<pre><code>loadstring(game:HttpGet("https://raw.githubusercontent.com/Liberator481993/MM2HUB/refs/heads/main/MM2HUB"))()</code></pre>');
    else if(item.file_id) {
      const file=await tg(env,"sendDocument",{chat_id:chat,document:item.file_id,caption:item.file_name||undefined});
      if(!file.ok) console.error("Document delivery failed",file.description);
    }
    return;
  }
  if(data==="profile")return send(env,chat,`👤 <b>Profile</b>\nID: <code>${id}</code>\nLanguage: ${lang}`);
  if(!admins(env).has(String(id))) return send(env,chat,tr(lang,"denied"));
  if(data==="adm:home")return send(env,chat,tr(lang,"admin_title"),{reply_markup:kb([[btn(lang==="ru"?"📢 Создать пост в канал":"📢 Create channel post","adm:channel_post")],[btn(tr(lang,"content"),"adm:content")],[btn(tr(lang,"broadcast"),"adm:broadcast")],[btn(tr(lang,"stats"),"adm:stats")],[btn(tr(lang,"back"),"nav:home")]])});
  if(data==="adm:content")return send(env,chat,tr(lang,"cat"),{reply_markup:kb([["scripts","injectors","guides"].map(x=>btn(tr(lang,x),`adm:cat:${x}`)),[btn(tr(lang,"back"),"adm:home")]])});
  if(data==="adm:channel_post"){await setState(env,id,"post_text",{});return send(env,chat,lang==="ru"?"Отправь текст поста для канала:":"Send the channel post text:");}
  if(data==="adm:post:cancel"){await clearState(env,id);return send(env,chat,lang==="ru"?"Публикация отменена.":"Post cancelled.");}
  if(data.startsWith("adm:post:style:")){
    const style=data.split(":")[3];
    if(!["primary","success","danger"].includes(style))return send(env,chat,tr(lang,"invalid"));
    const st=await state(env,id); let d={};try{d=JSON.parse(st?.data||"{}")}catch{}
    if(st?.step!=="post_style")return send(env,chat,lang==="ru"?"Черновик публикации устарел. Начни заново.":"The post draft expired. Start again.");
    d.post_button_style=style;
    await setState(env,id,"post_confirm",d);
    const me=await tg(env,"getMe",{});
    if(!me.ok||!me.result.username){await clearState(env,id);return send(env,chat,tr(lang,"invalid"));}
    const markup=kb([[{text:d.post_button,url:"https://t.me/"+me.result.username+"?start=home",style}]]);
    if(d.post_photo_id) await tg(env,"sendPhoto",{chat_id:chat,photo:d.post_photo_id,caption:d.post_text,reply_markup:markup});
    else await send(env,chat,esc(d.post_text),{reply_markup:markup});
    return send(env,chat,lang==="ru"?"Предпросмотр готов. Нажми «Опубликовать» или /cancel.":"Preview ready. Press Publish or /cancel.",{reply_markup:kb([[btn(lang==="ru"?"🚀 Опубликовать":"🚀 Publish","adm:post:publish")],[btn(lang==="ru"?"✖️ Отмена":"✖️ Cancel","adm:post:cancel")]])});
  }
  if(data==="adm:post:publish"){
    const st=await state(env,id); let d={};try{d=JSON.parse(st?.data||"{}")}catch{}
    if(st?.step!=="post_confirm")return send(env,chat,lang==="ru"?"Черновик не найден.":"Draft not found.");
    const me=await tg(env,"getMe",{});
    if(!me.ok||!me.result.username)return send(env,chat,tr(lang,"invalid"));
    const markup=kb([[{text:d.post_button,url:"https://t.me/"+me.result.username+"?start=home",style:d.post_button_style||"primary"}]]);
    const r=d.post_photo_id
      ? await tg(env,"sendPhoto",{chat_id:env.CHANNEL_ID||"@mm2hubscripts",photo:d.post_photo_id,caption:d.post_text,reply_markup:markup})
      : await send(env,env.CHANNEL_ID||"@mm2hubscripts",esc(d.post_text),{reply_markup:markup});
    if(!r.ok)return send(env,chat,lang==="ru"?"Не удалось опубликовать. Проверь права бота в канале.":"Publish failed. Check the bot's channel permissions.");
    await clearState(env,id);return send(env,chat,lang==="ru"?"✅ Пост опубликован в канале.":"✅ Channel post published.");
  }
  if(data.startsWith("adm:cat:")) {const cat=data.split(":")[2]; if(!CATALOGS[cat])return; const rows=CATALOGS[cat].map(([slug,title])=>[btn(title,`adm:edit:${cat}:${slug}`),btn(tr(lang,"del"),`adm:del:${cat}:${slug}`)]);rows.push([btn(tr(lang,"back"),"adm:content")]);return send(env,chat,tr(lang,"item"),{reply_markup:kb(rows)});}
  if(data.startsWith("adm:edit:")) {const [, ,cat,slug]=data.split(":");if(!CATALOGS[cat]?.some(x=>x[0]===slug))return;await setState(env,id,"title_ru",{category:cat,slug});return send(env,chat,tr(lang,"title_ru"));}
  if(data.startsWith("adm:del:")) {const [, ,cat,slug]=data.split(":");await env.DB.prepare("DELETE FROM content_items WHERE category=? AND slug=?").bind(cat,slug).run();return send(env,chat,tr(lang,"deleted"));}
  if(data==="adm:broadcast"){await setState(env,id,"broadcast");return send(env,chat,tr(lang,"broadcast_q"));}
  if(data==="adm:stats"){const a=await env.DB.prepare("SELECT COUNT(*) n FROM users").first(),b=await env.DB.prepare("SELECT COUNT(*) n FROM content_items").first();return send(env,chat,tr(lang,"stats_text").replace("{users}",a.n).replace("{content}",b.n));}
}
async function health(env) {
  if (!env.DB || typeof env.DB.prepare !== "function") {
    return Response.json({status:"error",database:"unavailable"},{status:503});
  }
  try {
    await env.DB.prepare("SELECT 1 AS ok").first();
    return Response.json({status:"ok",database:"ok"});
  } catch (error) {
    console.error("Health check failed", error);
    return Response.json({status:"error",database:"unavailable"},{status:503});
  }
}

async function claimUpdate(env, updateId) {
  // A short lease lets Telegram retries recover from a Worker crash while
  // preventing concurrent delivery of the same update in normal operation.
  return env.DB.prepare(
    "INSERT INTO processed_updates(update_id,status,updated_at) VALUES(?,'processing',CURRENT_TIMESTAMP) " +
    "ON CONFLICT(update_id) DO UPDATE SET status='processing',updated_at=CURRENT_TIMESTAMP " +
    "WHERE processed_updates.status='failed' OR processed_updates.updated_at < datetime('now','-5 minutes') " +
    "RETURNING update_id"
  ).bind(updateId).first();
}

export default {
  async fetch(request,env) {
    const url=new URL(request.url);
    if(request.method==="GET"&&url.pathname==="/")return new Response("LiberiumBot Cloudflare Worker is running.");
    if(request.method==="GET"&&url.pathname==="/healthz")return health(env);
    if(request.method!=="POST"||url.pathname!=="/telegram/webhook")return new Response("Not found",{status:404});

    if(!env.BOT_TOKEN || !env.WEBHOOK_SECRET || !env.DB) {
      console.error("Webhook configuration is incomplete.");
      return new Response("Service unavailable",{status:503});
    }
    if(request.headers.get("X-Telegram-Bot-Api-Secret-Token")!==env.WEBHOOK_SECRET) {
      return new Response("Unauthorized",{status:401});
    }

    let update;
    try { update=await request.json(); }
    catch { return new Response("Bad request",{status:400}); }
    if(!Number.isSafeInteger(update?.update_id) || update.update_id<0) {
      return new Response("Invalid update",{status:400});
    }

    try {
      const claim=await claimUpdate(env,update.update_id);
      if(!claim) return new Response("Duplicate update",{status:200});
      if(update.message) await handleMessage(env,update.message);
      else if(update.callback_query) await handleCallback(env,update.callback_query);
      await env.DB.prepare("UPDATE processed_updates SET status='processed',updated_at=CURRENT_TIMESTAMP WHERE update_id=?").bind(update.update_id).run();
      return new Response("OK");
    } catch(error) {
      console.error("Update handler failed",error);
      try {
        await env.DB.prepare("UPDATE processed_updates SET status='failed',updated_at=CURRENT_TIMESTAMP WHERE update_id=?").bind(update.update_id).run();
      } catch(markError) {
        console.error("Could not mark Telegram update as failed",markError);
      }
      // A non-2xx response asks Telegram to retry the update.
      return new Response("Temporary processing failure",{status:503});
    }
  }
};
