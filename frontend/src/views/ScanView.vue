<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '../components/PageHeader.vue'
const router=useRouter(), manual=ref(''), scanning=ref(false), supported=ref('BarcodeDetector' in window), video=ref(null)
let stream, timer
function openValue(value){ const m=String(value).match(/LAB-YUANLIAO:(\d+)/i) || String(value).match(/(?:chemicals\/)?(\d+)$/); if(!m) return alert('无法识别该二维码内容'); stop(); router.push(`/chemicals/${m[1]}`) }
async function start(){
  if(!supported.value) return; try{ stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}}); video.value.srcObject=stream; await video.value.play(); scanning.value=true; const detector=new BarcodeDetector({formats:['qr_code']});
  timer=setInterval(async()=>{ try{ const codes=await detector.detect(video.value); if(codes[0]?.rawValue) openValue(codes[0].rawValue) }catch{} },500)
  }catch(e){ alert(`无法打开摄像头：${e.message}`) }
}
function stop(){ scanning.value=false; if(timer) clearInterval(timer); if(stream) stream.getTracks().forEach(t=>t.stop()) }
onBeforeUnmount(stop)
</script>
<template>
  <PageHeader title="扫码查询" subtitle="扫描系统生成的二维码，快速打开原料详情" />
  <section class="panel scan-panel">
    <div class="scanner-box"><video ref="video" playsinline></video><div v-if="!scanning" class="scanner-placeholder">QR</div></div>
    <div class="scan-actions">
      <template v-if="supported"><button v-if="!scanning" class="btn primary" @click="start">打开摄像头扫描</button><button v-else class="btn danger-btn" @click="stop">停止扫描</button></template>
      <p v-else class="muted">当前浏览器不支持 BarcodeDetector，可使用下面的手动编号查询。</p>
      <div class="manual-row"><input v-model="manual" class="input" placeholder="输入原料 ID 或 LAB-YUANLIAO:123" @keyup.enter="openValue(manual)" /><button class="btn ghost" @click="openValue(manual)">查询</button></div>
    </div>
  </section>
</template>
