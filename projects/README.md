# projects/

Raw layer — 프로젝트별 데이터와 코드를 여기에 넣는다.

```
projects/
└── {project_name}/
    ├── code/       ← 작업 노트북
    ├── data/       ← 데이터셋
    └── reference/  ← 참고 자료
```

이 디렉토리는 `.gitignore`에 포함되어 있어 Git에 올라가지 않는다.  
`bootstrap.py` 실행 전에 `projects/{project_name}/` 폴더가 존재해야 한다.
