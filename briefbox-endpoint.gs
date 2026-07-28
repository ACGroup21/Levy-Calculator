/**
 * BRIEF BOX — the endpoint
 * Arthur Curtis Education
 *
 * This is what receives a posted brief and turns it into an email in your inbox.
 * It runs inside your own Google account, so no third party ever holds a
 * learner's file — the brief goes from their browser to your inbox and nowhere
 * else. That is the whole reason for doing it this way rather than renting a
 * form service.
 *
 * ── HOW TO PUT IT LIVE ──────────────────────────────────────────────────────
 *  1. Go to  script.google.com  →  New project.
 *  2. Delete whatever is in the editor and paste this whole file in.
 *  3. Change DELIVER_TO below to the address you want briefs to land at.
 *  4. Save, then  Deploy  →  New deployment  →  type: Web app.
 *       Execute as:        Me
 *       Who has access:    Anyone            ← must be "Anyone", not "Anyone with Google account"
 *  5. Authorise it when Google asks (it will warn that the app is unverified —
 *     that is because it is yours and unpublished; continue).
 *  6. Copy the Web app URL. It ends in  /exec.  That URL is the ENDPOINT.
 *
 * ── WHAT ARRIVES ────────────────────────────────────────────────────────────
 *   From:      the Google account running this script
 *   Reply-To:  the apprentice — so hitting reply goes to them
 *   Subject:   [BRIEF] Employer — Programme — J. Smith
 *   Body:      name, work email, employer, programme
 *   Attached:  the brief itself, as a real attachment
 */

/* ── settings ─────────────────────────────────────────────────────────────── */

var DELIVER_TO   = 'assignments@arthurcurtis.com';   // ← where briefs land
var SENDER_NAME  = 'Brief Box';                      // shows in your inbox
var MAX_BYTES    = 10 * 1024 * 1024;                 // must match the page
var ALLOWED_EXT  = ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'];

/* ── the endpoint ─────────────────────────────────────────────────────────── */

function doPost(e) {
  try {
    var d = JSON.parse(e.postData.contents);

    /* Validate here as well as in the page. The page's checks are a courtesy to
       the apprentice; these are the ones that actually hold, because anything
       can POST to this URL. */
    var name    = clean(d.name,      80);
    var email   = clean(d.email,    120);
    var company = clean(d.company,   90);
    var prog    = clean(d.programme, 120);

    if (name.length    < 2) return no('name');
    if (company.length < 2) return no('company');
    if (!prog)              return no('programme');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return no('email');
    if (d.website)          return ok();     // honeypot: a bot. Accept, bin it.

    var fname = clean(d.filename, 160) || 'brief';
    var ext   = (fname.split('.').pop() || '').toLowerCase();
    if (ALLOWED_EXT.indexOf(ext) === -1) return no('file type');

    var bytes = Utilities.base64Decode(d.file);
    if (!bytes.length)             return no('empty file');
    if (bytes.length > MAX_BYTES)  return no('file too large');

    var blob = Utilities.newBlob(bytes, d.mime || 'application/octet-stream', fname);

    MailApp.sendEmail({
      to:       DELIVER_TO,
      replyTo:  email,                 /* reply goes to the apprentice */
      name:     SENDER_NAME,
      subject:  subject(company, prog, name),
      body:     body(name, email, company, prog, fname, bytes.length),
      attachments: [blob]
    });

    return ok();

  } catch (err) {
    /* Never leak the internals to a browser; log it where only you can see. */
    console.error(err);
    return json({ ok: false, error: 'failed' });
  }
}

/* A GET is someone pasting the URL into a browser. Say what it is, do nothing. */
function doGet() {
  return ContentService
    .createTextOutput('Arthur Curtis — Brief Box endpoint. Nothing to see here.')
    .setMimeType(ContentService.MimeType.TEXT);
}

/* ── the shape of what arrives ────────────────────────────────────────────── */

/* Written here rather than by the sender, so every brief lands in the same
   shape and an inbox rule can rely on it. */
function subject(company, prog, name) {
  return '[BRIEF] ' + company + ' — ' + stripLevel(prog) + ' — ' + shortName(name);
}

function body(name, email, company, prog, fname, size) {
  return [
    'A brief has been posted through the Brief Box.',
    '',
    'Name:       ' + name,
    'Email:      ' + email,
    'Employer:   ' + company,
    'Programme:  ' + prog,
    '',
    'Attached:   ' + fname + '  (' + kb(size) + ')',
    '',
    'Reply to this email to go straight back to the apprentice.'
  ].join('\n');
}

/* ── small helpers ────────────────────────────────────────────────────────── */

function clean(v, max) {
  return String(v == null ? '' : v).replace(/[\r\n\t]+/g, ' ').trim().slice(0, max);
}
function stripLevel(p){ return p.replace(/^L\d\s/, ''); }
function shortName(n) {
  var p = n.split(/\s+/);
  return p.length > 1 ? p[0].charAt(0).toUpperCase() + '. ' + p[p.length - 1] : p[0];
}
function kb(n) {
  if (n < 1024)        return n + ' bytes';
  if (n < 1024 * 1024) return Math.max(1, Math.round(n / 1024)) + ' KB';
  return (n / 1048576).toFixed(1) + ' MB';
}
function json(o) {
  return ContentService.createTextOutput(JSON.stringify(o))
    .setMimeType(ContentService.MimeType.JSON);
}
function ok()      { return json({ ok: true }); }
function no(what)  { return json({ ok: false, error: what }); }

/* ── run this once from the editor to prove it works ──────────────────────────
   Sends yourself a test brief without involving the page at all. If this lands,
   the mail half is sound and anything still failing is the browser half. */
function testSend() {
  MailApp.sendEmail({
    to: DELIVER_TO,
    replyTo: 'test@example.com',
    name: SENDER_NAME,
    subject: subject('Landmark Group', 'L3 Business administrator', 'Jane Okonkwo'),
    body: body('Jane Okonkwo', 'test@example.com', 'Landmark Group',
               'L3 Business administrator', 'Unit 4 brief.txt', 184000),
    attachments: [Utilities.newBlob('This is a test brief.', 'text/plain', 'Unit 4 brief.txt')]
  });
}
