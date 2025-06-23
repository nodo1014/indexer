<script>
  // 버전 정보
  const version = '0.1.0';
</script>

<div class="p-4">
  <h1 class="text-2xl font-bold mb-6">About</h1>
  
  <div class="space-y-8">
    <!-- 소개 -->
    <section class="card">
      <h2 class="text-lg font-semibold mb-4">Whisper 자막 생성기</h2>
      
      <p class="mb-4">
        이 애플리케이션은 NAS에 저장된 미디어 파일을 효율적으로 관리하고,
        자막이 없는 파일들에 대해 OpenAI의 Whisper 모델을 활용하여 고품질 자막을 자동으로 생성해주는 도구입니다.
      </p>
      
      <p class="mb-2">주요 기능:</p>
      <ul class="list-disc list-inside mb-4 space-y-1 pl-4">
        <li>NAS 디렉토리 탐색 및 미디어 파일 관리</li>
        <li>Whisper AI를 활용한 음성 자막 생성</li>
        <li>자막 싱크 자동 검증 및 조정</li>
        <li>외부 자막 자동 다운로드</li>
        <li>실시간 작업 현황 모니터링</li>
      </ul>
      
      <div class="text-sm text-gray-500 dark:text-gray-400">
        버전: {version}
      </div>
    </section>
    
    <!-- 기술 스택 -->
    <section class="card">
      <h2 class="text-lg font-semibold mb-4">기술 스택</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 class="font-medium mb-2">프론트엔드</h3>
          <ul class="list-disc list-inside space-y-1 pl-4">
            <li>SvelteKit</li>
            <li>TypeScript</li>
            <li>TailwindCSS</li>
            <li>WebSockets</li>
          </ul>
        </div>
        
        <div>
          <h3 class="font-medium mb-2">백엔드</h3>
          <ul class="list-disc list-inside space-y-1 pl-4">
            <li>Python</li>
            <li>FastAPI</li>
            <li>Whisper AI</li>
            <li>FFmpeg</li>
            <li>OpenSubtitles API</li>
          </ul>
        </div>
      </div>
    </section>
    
    <!-- 사용법 -->
    <section class="card">
      <h2 class="text-lg font-semibold mb-4">사용법</h2>
      
      <div class="space-y-4">
        <div>
          <h3 class="font-medium mb-2">1. 디렉토리 탐색</h3>
          <p>
            좌측의 디렉토리 탐색기를 사용하여 NAS 내 미디어 파일이 있는 폴더로 이동합니다.
            각 폴더에는 해당 폴더 내 비디오와 오디오 파일 개수가 표시됩니다.
          </p>
        </div>
        
        <div>
          <h3 class="font-medium mb-2">2. 미디어 파일 선택</h3>
          <p>
            자막을 생성할 미디어 파일을 선택합니다. 파일 목록에서 체크박스를 사용하여 여러 파일을 한 번에 선택할 수 있습니다.
          </p>
        </div>
        
        <div>
          <h3 class="font-medium mb-2">3. Whisper 설정 및 실행</h3>
          <p>
            언어와 모델을 선택한 후 "Whisper 자막 생성" 버튼을 클릭합니다.
            모델 크기에 따라 처리 속도와 정확도가 달라집니다.
          </p>
        </div>
        
        <div>
          <h3 class="font-medium mb-2">4. 작업 모니터링</h3>
          <p>
            왼쪽 패널에서 진행 중인 작업의 상태와 진행률을 실시간으로 확인할 수 있습니다.
            필요에 따라 작업을 일시정지하거나 취소할 수 있습니다.
          </p>
        </div>
        
        <div>
          <h3 class="font-medium mb-2">5. 자막 싱크 검증</h3>
          <p>
            생성된 자막의 싱크를 검증하고 필요한 경우 조정하려면 상단 메뉴에서 "자막 싱크 검증" 페이지로 이동합니다.
            미디어 파일과 자막 파일을 선택한 후 "싱크 검증 시작" 버튼을 클릭합니다.
          </p>
        </div>
      </div>
    </section>
    
    <!-- 연락처 및 기여 -->
    <section class="card">
      <h2 class="text-lg font-semibold mb-4">연락처 및 기여</h2>
      
      <p class="mb-4">
        이 프로젝트는 오픈 소스로 개발되고 있으며, 개선 사항 제안이나 버그 신고는 GitHub 저장소를 통해 가능합니다.
      </p>
      
      <div class="flex justify-center">
        <a 
          href="https://github.com/nodo1014/indexer" 
          class="btn btn-primary"
          target="_blank" 
          rel="noopener noreferrer"
        >
          GitHub 저장소 방문
        </a>
      </div>
    </section>
  </div>
</div> 