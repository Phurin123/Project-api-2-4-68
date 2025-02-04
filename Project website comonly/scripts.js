// ฟังก์ชันสำหรับอัปโหลดภาพ
function uploadImage() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';

  input.onchange = async () => {
    const file = input.files[0];
    if (!file) return;

    // สร้าง FormData สำหรับส่งภาพไปยัง API
    const formData = new FormData();
    formData.append('image', file);

    // แสดงสถานะโหลด
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultText = document.getElementById('resultText');
    const imagePreview = document.getElementById('imagePreview');
    loadingSpinner.style.display = 'block';
    resultText.textContent = ''; // ล้างข้อความผลลัพธ์

    // แสดงภาพที่เลือก
    const reader = new FileReader();
    reader.onload = () => {
      imagePreview.src = reader.result;
      imagePreview.style.display = 'block';
    };
    reader.readAsDataURL(file);

    try {
      // เรียก API เพื่อวิเคราะห์ภาพ
      const response = await fetch('http://127.0.0.1:5000/analyze-image', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      // ซ่อนสถานะโหลด
      loadingSpinner.style.display = 'none';

      if (response.ok) {
        // แสดงผลลัพธ์
        const detectionsPorn = data.detections_porn;
        const detectionsWeapon = data.detections_weapon;

        if (detectionsPorn.length === 0 && detectionsWeapon.length === 0) {
          resultText.textContent = 'ผลลัพธ์: ผ่าน';
          resultText.className = 'pass';
        } else {
          resultText.textContent = 'ผลลัพธ์: ไม่ผ่าน';
          resultText.className = 'fail';

          // แสดงรายละเอียดของวัตถุที่ตรวจจับได้
          let detectionDetails = '';
          if (detectionsPorn.length > 0) {
            detectionDetails += 'พบวัตถุไม่เหมาะสมในภาพ: ';
            detectionsPorn.forEach((detection) => {
              detectionDetails += `${detection.label} (ความมั่นใจ: ${detection.confidence.toFixed(2)})\n`;
            });
          }

          if (detectionsWeapon.length > 0) {
            detectionDetails += 'พบอาวุธในภาพ: ';
            detectionsWeapon.forEach((detection) => {
              detectionDetails += `${detection.label} (ความมั่นใจ: ${detection.confidence.toFixed(2)})\n`;
            });
          }

          resultText.textContent += detectionDetails;
        }
      } else {
        // แสดงข้อผิดพลาด
        resultText.textContent = `ข้อผิดพลาด: ${data.error || 'เกิดข้อผิดพลาดในการวิเคราะห์'}`;
        resultText.className = 'fail';
      }
    } catch (error) {
      // แสดงข้อผิดพลาด
      loadingSpinner.style.display = 'none';
      resultText.textContent = 'ข้อผิดพลาด: ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์';
      resultText.className = 'fail';
    }
  };

  input.click();
}

// ฟังก์ชันขอ API Key
function requestApiKey() {
  const email = prompt('กรุณาใส่อีเมลของคุณเพื่อขอ API Key:');
  if (!email) return;
 
  fetch('http://127.0.0.1:5000/request-api-key', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.apiKey) {
        alert(`API Key ของคุณคือ: ${data.apiKey}`);
      } else {
        alert(`ข้อผิดพลาด: ${data.error}`);
      }
    })
    .catch(() => {
      alert('ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์');
    });
}

// ฟังก์ชันรายงานปัญหา
function reportIssue() {
  const issueDescription = prompt('กรุณาระบุรายละเอียดปัญหาที่คุณพบ:');
  if (!issueDescription) return;

  // ส่งข้อมูลไปยังเซิร์ฟเวอร์หรืออีเมล
  fetch('http://127.0.0.1:5000/report-issue', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ issue: issueDescription }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert('ขอบคุณสำหรับการรายงานปัญหาของคุณ!');
      } else {
        alert('ไม่สามารถส่งข้อมูลได้ กรุณาลองใหม่อีกครั้ง');
      }
    })
    .catch(() => {
      alert('ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์');
    });
}

// ฟังก์ชันสำหรับดาวน์โหลดเอกสารคู่มือ
function downloadManual() {
  const url = "https://example.com/path/to/manual.pdf"; // แก้ไขให้เป็นพาธของไฟล์เอกสารที่คุณเตรียมไว้
  const link = document.createElement('a');
  link.href = url;
  link.download = 'คู่มือการใช้งาน.pdf'; // ชื่อไฟล์ที่ผู้ใช้จะดาวน์โหลด
  link.click();
}





























