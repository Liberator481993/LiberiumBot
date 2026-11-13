import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

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
