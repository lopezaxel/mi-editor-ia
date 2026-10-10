/* ==========================================================================
   CAEIA helpers for HyperFrames compositions (seek-safe: built once at load,
   only tl.set / tl.to / tl.fromTo). Load after gsap and kit/premium.js.

     CAEIA.json("transcript")              // parse <script type="application/json" id="transcript">
     CAEIA.captions(tl, words, opts)       // word-by-word captions from transcript.json [{text,start,end}]
     CAEIA.wordmark("#wm")                 // CAE (blue) | IA (violet), literal split
     const cam = CAEIA.cam(tl, "#cam", 1080, 1920);  cam(t, [x, y], scale)
     (register the root timeline inline in the page: the HyperFrames linter looks for it literally)
   ========================================================================== */
(function (root) {
  const C = {};
  const $ = (s) => (typeof s === "string" ? document.querySelector(s) : s);

  C.json = (id) => {
    const el = document.getElementById(id);
    return el ? JSON.parse(el.textContent || "null") : null;
  };

  // Camera on the #cam world: brings world point [wx, wy] to the frame centre at scale s.
  C.cam = (tl, sel, W, H) => (t, [wx, wy], s, d = 0.9, ease = "expo.inOut") =>
    tl.to(sel, { x: W / 2 - wx * s, y: H / 2 - wy * s, scale: s, duration: d, ease }, t);

  C.wordmark = (sel) => { $(sel).innerHTML = '<span class="cae">CAE</span><span class="ia">IA</span>'; };

  // Split words into caption lines: break on sentence punctuation, on a pause, or at maxWords.
  C.groupWords = (words, { maxWords = 4, maxGap = 0.6 } = {}) => {
    const lines = []; let cur = [];
    words.forEach((w, i) => {
      if (!String(w.text).trim()) return;
      cur.push(w);
      const next = words[i + 1];
      const endsSentence = /[.!?…,;:]$/.test(String(w.text).trim());
      const pause = next ? next.start - w.end > maxGap : true;
      if (cur.length >= maxWords || endsSentence || pause) { lines.push(cur); cur = []; }
    });
    if (cur.length) lines.push(cur);
    return lines;
  };

  // Word-by-word captions. Each line pops in at its first word, the spoken word turns brand blue,
  // the line leaves when the next one starts (or `hold` s after its last word).
  // offset = composition time where transcript time 0 lands (footage data-start minus data-media-start).
  C.captions = (tl, words, o = {}) => {
    const box = $(o.el || "#subs"), off = o.offset ?? 0, hold = o.hold ?? 0.35;
    const lines = C.groupWords(words || [], o);
    lines.forEach((ln, li) => {
      const div = document.createElement("div");
      div.className = "cap-line"; div.id = "cap" + li;
      div.innerHTML = ln.map((w, wi) => `<span class="cw" id="cap${li}w${wi}" data-on="0">${String(w.text).trim()}</span>`).join(" ");
      box.appendChild(div);
      const t0 = off + ln[0].start, nextStart = lines[li + 1] ? off + lines[li + 1][0].start : Infinity;
      const t1 = Math.min(off + ln[ln.length - 1].end + hold, nextStart);
      tl.fromTo(div, { autoAlpha: 0, y: 16 }, { autoAlpha: 1, y: 0, duration: 0.16, ease: "expo.out" }, t0);
      tl.set(div, { autoAlpha: 0 }, t1);
      ln.forEach((w, wi) => {
        const sp = `#cap${li}w${wi}`;
        tl.set(sp, { attr: { "data-on": "1" } }, off + w.start);
        tl.set(sp, { attr: { "data-on": "0" } }, wi + 1 < ln.length ? off + ln[wi + 1].start : t1);
      });
    });
    return lines.length;
  };


  root.CAEIA = C;
})(window);
