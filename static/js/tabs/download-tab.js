// ...existing code in downloadSubtitle method...
-            const response = await fetch('/api/download_subtitle', {
-                method: 'POST',
-                headers: {
-                    'Content-Type': 'application/json',
-                },
-                body: JSON.stringify({
-                    media_path: filePath,
-                    filename: fileName,
-                    language: language
-                }),
-            });
-            
-            const data = await response.json();
-            
-            if (!response.ok || data.error) {
-                throw new Error(data.error || '알 수 없는 오류');
-            }
+            const response = await fetch('/api/download_subtitle', {
+                method: 'POST',
+                headers: {
+                    'Content-Type': 'application/json',
+                },
+                body: JSON.stringify({
+                    media_path: filePath,
+                    filename: fileName,
+                    language: language
+                }),
+            });
+            
+            // 응답 JSON 파싱 시도
+            let data;
+            try {
+                data = await response.json();
+            } catch (e) {
+                data = null;
+            }
+            
+            // HTTP 상태코드 기반 오류 처리
+            if (!response.ok) {
+                let errMsg = `오류 ${response.status}: ${response.statusText}`;
+                if (response.status === 403) {
+                    errMsg = 'API 호출 권한 오류(403): OpenSubtitles API 키를 확인하세요.';
+                }
+                throw new Error((data && data.error) ? data.error : errMsg);
+            }
+            // API 레벨 오류
+            if (data && data.error) {
+                throw new Error(data.error);
+            }
 // ...existing code continues...