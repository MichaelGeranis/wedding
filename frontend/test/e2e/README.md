Run the simple E2E backend connectivity check:

Set the backend URL and run the npm script from the `frontend` folder:

```bash
cd frontend
VITE_API_BASE_URL=http://localhost:8000 npm run test:e2e
```

The script calls `/api/health` and exits with code 0 on success.
The script calls `/health` and exits with code 0 on success.
