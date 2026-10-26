#!/usr/bin/env node
'use strict';

const fs = require('fs');
const { JSDOM } = require('jsdom');
const html = fs.readFileSync(require('path').join(__dirname, '..', 'digylog-chat.html'), 'utf8');
const calls = [];
const conversation = {
  id: 50932,
  traking: 'S3900385FA',
  createdAt: '2025-01-21T11:37:23+01:00',
  updatedAt: '2025-01-21T11:54:47+01:00',
  user: 'ABDO',
  closed: false
};
const messages = [{
  id: 189975,
  content: 'test officiel',
  createdAt: '2025-01-21T11:37:23+01:00',
  sender: 'ABDO',
  profil: '2',
  status: 'read'
}];

function response(payload, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload
  });
}

(async () => {
  const dom = new JSDOM(html, {
    url: 'https://crm.test/digylog-chat.html?compact=1&tracking=S3900385FA&viewerId=1&v=4',
    runScripts: 'dangerously',
    resources: 'usable',
    pretendToBeVisual: true,
    beforeParse(window) {
      window.setInterval = () => 0;
      window.fetch = async (_url, options) => {
        const body = JSON.parse(options.body);
        calls.push(body);
        if (body.action === 'digylog_chat_direct') {
          return response({ok: true, tracking: 'S3900385FA', conversation, payload: messages});
        }
        if (body.action === 'digylog_chat_send') return response({ok: true, result: {id: 189976}});
        if (body.action === 'digylog_chat_history') {
          return response({ok: true, tracking: 'S3900385FA', conversation, payload: messages});
        }
        return response({ok: false, err: 'unexpected-action'}, 400);
      };
    }
  });

  await new Promise(resolve => setTimeout(resolve, 100));
  const doc = dom.window.document;
  if (!doc.querySelector('.chat-head h2')?.textContent.includes('S3900385FA')) throw new Error('exact Tracking was not rendered');
  if (!doc.querySelector('.msg-text')?.textContent.includes('test officiel')) throw new Error('official content field was not rendered');
  if (!doc.querySelector('.msg-row.out')) throw new Error('official profil=2 message was not rendered as seller message');
  if (doc.getElementById('message').disabled) throw new Error('open conversation composer stayed disabled');
  if (!calls.some(c => c.action === 'digylog_chat_direct' && c.tracking === 'S3900385FA' && String(c.viewerId) === '1')) throw new Error('direct request contract is wrong');

  doc.getElementById('message').value = 'réponse test';
  doc.getElementById('composer').dispatchEvent(new dom.window.Event('submit', {bubbles: true, cancelable: true}));
  await new Promise(resolve => setTimeout(resolve, 100));
  const send = calls.find(c => c.action === 'digylog_chat_send');
  if (!send || send.tracking !== 'S3900385FA' || String(send.chatId) !== '50932' || send.message !== 'réponse test') throw new Error('send request contract is wrong');

  dom.window.close();

  const searchCalls = [];
  const searchDom = new JSDOM(html, {
    url: 'https://crm.test/digylog-chat.html?embed=1&viewerId=1&v=5',
    runScripts: 'dangerously',
    resources: 'usable',
    pretendToBeVisual: true,
    beforeParse(window) {
      window.setInterval = () => 0;
      window.fetch = async (_url, options) => {
        const body = JSON.parse(options.body);
        searchCalls.push(body);
        if (body.action === 'digylog_chat_list') return response({ok: true, viewer: {role: 'admin', agent: ''}, conversations: [conversation]});
        return response({ok: false, err: 'unexpected-action'}, 400);
      };
    }
  });
  await new Promise(resolve => setTimeout(resolve, 100));
  const search = searchDom.window.document.getElementById('search');
  search.value = 's3900385fa';
  search.dispatchEvent(new searchDom.window.Event('input', {bubbles: true}));
  await new Promise(resolve => setTimeout(resolve, 450));
  if (!searchCalls.some(c => c.action === 'digylog_chat_list' && c.tracking === 'S3900385FA')) throw new Error('full Chat search did not query the exact Tracking');
  if (!searchDom.window.document.querySelector('.conv-title')?.textContent.includes('S3900385FA')) throw new Error('searched conversation was not rendered');
  searchDom.window.close();

  console.log('PASS  Digylog Chat browser flow: exact popup, remote search, official messages, reply');
})().catch(error => {
  console.error(error.stack || error);
  process.exit(1);
});
