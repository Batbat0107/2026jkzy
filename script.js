// 泛光小球聊天机器人 - p5.js 实现
let robot;
let messages = ["嗨！我是泛光小球。请把 JSONBin 链接粘贴到输入框。", "我能用文字驱动口型并在头顶显示字幕。"];
let currentMsg = '';
let msgIndex = 0;
let playing = false;
let speechTimeline = [];
let timelineIdx = 0;
let lastStepTime = 0;
let bubbleEl;
let statusEl;
let autoPlayEl;
let fetchBtn, binUrlEl, apiKeyEl;
let lastAutoTime = 0; // 用于自动播放节流

function setup(){
  const canvas = createCanvas(720,480);
  canvas.parent('sketch-container');
  angleMode(DEGREES);
  robot = new Robot(width/2, height*0.6, 160);

  // UI hooks
  bubbleEl = createDiv('').addClass('bubble');
  bubbleEl.position((width/2 - bubbleEl.width/2)+canvas.position().x, 40+canvas.position().y);
  statusEl = select('#status');
  fetchBtn = select('#fetchBtn');
  binUrlEl = select('#binUrl');
  apiKeyEl = select('#apiKey');
  autoPlayEl = select('#autoPlay');

  fetchBtn.mousePressed(fetchNextMessage);

  // 支持通过 URL 参数预填充，例如: ?binUrl=...&apiKey=...&auto=1
  const params = new URLSearchParams(window.location.search);
  const pBin = params.get('binUrl') || params.get('BIN_URL');
  if(pBin) binUrlEl.value(pBin);
  else binUrlEl.value('https://api.jsonbin.io/v3/b/695b5bd043b1c97be919ec3d/latest'); // 默认示例私有 bin
  const pKey = params.get('apiKey') || params.get('BIN_KEY');
  if(pKey) apiKeyEl.value(pKey);
  if(params.get('auto') === '1') autoPlayEl.elt.checked = true;

  setMessage(messages[0]);
}

function windowResized(){
  const container = select('#sketch-container');
  const w = container.width;
  const h = container.height;
  resizeCanvas(w,h);
  robot.pos.x = width/2;
  robot.pos.y = height*0.6;
  bubbleEl.position((width/2 - bubbleEl.width/2)+select('#sketch-container').elt.getBoundingClientRect().left, 40+select('#sketch-container').elt.getBoundingClientRect().top);
}

function draw(){
  clear();
  background(10,18,40, 120);
  robot.update();
  robot.draw();

  // 自动播放：若选中且不在发言中，根据时间与文本长度发下一条
  if(autoPlayEl && autoPlayEl.elt && autoPlayEl.elt.checked && !playing && millis() - lastAutoTime > (800 + (currentMsg?currentMsg.length*30:0))){
    fetchNextMessage();
    lastAutoTime = millis();
  }

  // advance timeline
  if(playing && speechTimeline.length){
    const now = millis();
    if(now - lastStepTime > speechTimeline[timelineIdx].dur){
      timelineIdx++;
      lastStepTime = now;
      if(timelineIdx >= speechTimeline.length){
        playing = false;
        statusEl.html('状态：空闲');
      } else {
        robot.setMouth(speechTimeline[timelineIdx].open);
      }
    }
  }

  // bubble text (show current message)
  bubbleEl.html(currentMsg);
}

class Robot{
  constructor(x,y,r){
    this.pos = createVector(x,y);
    this.r = r;
    this.mouthOpen = 0; // visible mouth openness (smoothed)
    this.targetMouthOpen = 0; // target value set by timeline
    this.eyeOffset = r*0.2;
    this.glowColor = color(86,204,242);
  }

  setMouth(v){
    this.targetMouthOpen = constrain(v,0,1);
  }

  update(){
    // subtle breathing
    const t = millis()/1000;
    this.swell = 1 + 0.02 * sin(t*1.6);
    // smooth mouth easing
    this.mouthOpen = lerp(this.mouthOpen, this.targetMouthOpen, 0.22);
  }

  draw(){
    push();
    translate(this.pos.x, this.pos.y);
    scale(this.swell);

    // glow (draw concentric ellipses)
    noStroke();
    for(let i=12;i>=1;i--){
      const alpha = map(i,1,12,6,80);
      fill(red(this.glowColor), green(this.glowColor), blue(this.glowColor), alpha);
      ellipse(0,0, this.r + i*28, this.r + i*28);
    }

    // core sphere
    fill(10,28,50);
    ellipse(0,0,this.r,this.r);

    // eyes
    fill(255);
    ellipse(-this.eyeOffset, -this.r*0.15, this.r*0.22, this.r*0.22);
    ellipse(this.eyeOffset, -this.r*0.15, this.r*0.22, this.r*0.22);
    fill(12,18,30);
    ellipse(-this.eyeOffset, -this.r*0.15, this.r*0.1, this.r*0.1);
    ellipse(this.eyeOffset, -this.r*0.15, this.r*0.1, this.r*0.1);

    // mouth: represented as rounded rectangle arc that opens vertically
    const mouthW = this.r*0.6;
    const mouthH = this.r*0.18 + this.mouthOpen*this.r*0.3;
    fill(20,90,120);
    rectMode(CENTER);
    ellipse(0, this.r*0.26, mouthW, mouthH, mouthH/2);

    pop();
  }
}

// ------- speech timeline generation -------
function buildTimelineFromText(txt){
  const timeline = [];
  for(let i=0;i<txt.length;i++){
    const ch = txt[i];
    const lower = ch.toLowerCase();
    let open = 0.5;
    if("aeiouüAEIOU".includes(lower)) open = 1.0;
    else if("mbpwyfv".includes(lower)) open = 0.25;
    else if(lower === ' ') open = 0.0;
    else open = 0.5;

    const dur = 50 + (Math.random()*60); // per-char duration in ms
    timeline.push({open:open, dur:dur});
  }
  return timeline;
}

function setMessage(msg){
  currentMsg = msg;
  bubbleEl.html(currentMsg);
}

function speak(msg){
  setMessage(msg);
  // build timeline
  speechTimeline = buildTimelineFromText(msg);
  timelineIdx = 0;
  lastStepTime = millis();
  playing = true;
  robot.setMouth(speechTimeline[0].open);
  statusEl.html('状态：发言中');
}

// fetch messages from JSONBin or use sample
async function fetchNextMessage(){
  const url = binUrlEl.value().trim();
  const key = apiKeyEl.value().trim();
  if(!url){
    // use local sample messages in queue
    currentMsg = messages[msgIndex % messages.length];
    speak(currentMsg);
    msgIndex++;
    return;
  }
  statusEl.html('状态：从 JSONBin 获取中...');
  try{
    const headers = {};
    if(key) headers['X-Master-Key'] = key; // jsonbin v3
    const res = await fetch(url, {headers});
    if(!res.ok) throw new Error('Fetch failed: '+res.status);
    const data = await res.json();
    // JSONBin v3 可能会把真实数据放在 data.record 或 record 字段里。
    const payload = data.record || data.data || data;

    // expect an object like {messages: ['...'] } or an array
    let arr = [];
    if(Array.isArray(payload)) arr = payload;
    else if(Array.isArray(payload.messages)) arr = payload.messages;
    else if(Array.isArray(payload.data)) arr = payload.data;
    else {
      // try to find first array value
      for(const k in payload){ if(Array.isArray(payload[k])) {arr = payload[k]; break;} }
    }
    if(arr.length === 0) throw new Error('没有找到消息数组，请检查 JSON 结构');
    const m = arr[msgIndex % arr.length];
    msgIndex++;
    speak(m);
    // append to log
    const log = select('#log');
    if(log){
      const el = createDiv(m).addClass('item');
      log.child(el);
      // keep last 6
      while(log.elt.childNodes.length > 6) log.elt.removeChild(log.elt.firstChild);
    }
  }catch(err){
    statusEl.html('错误：' + err.message);
    console.error(err);
  }
}

// quick keyboard shortcuts for testing
function keyPressed(){
  if(key === ' ') fetchNextMessage();
}
