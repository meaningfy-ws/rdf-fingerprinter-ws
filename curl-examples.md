## Set of `curl` commands to test the `api`

### get fingerprinting reports info

```bash
curl --location --request GET 'localhost:4020/reports'
```

### fingerprint file

change `path-to-file` to the desired file.

```bash
curl --location --request POST 'localhost:4020/fingerprint-file' \
--form 'data_file=@"<path-to-file>"'
```

### fingerprint sparql endpoint

change `sparql-endpoint-url` to the desired url. `graphs` is optional.

```bash
curl --location --request POST 'localhost:4020/fingerprint-sparql-endpoint' \
--header 'Content-Type: application/json' \
--data-raw '{
    "sparql_endpoint_url": "<sparql-endpoint-url>",
    "graphs": ["graph1", "graph2"]
}'
```

### get specific fingerprinting

change `uid` to the desired fingerprinting id and `type` to one of the `html`, `json`, or `zip`.

```bash
curl --location --request GET 'localhost:4020/reports/<uid>?report_type=<type>'
```

### delete fingerprinting

change `uid` to the desired fingerprinting id.

```bash
curl --location --request DELETE 'localhost:4020/reports/<uid>
```

### delete all fingerprinting
```bash
curl --location --request DELETE 'localhost:4020/remove-reports'
```

### get active tasks
```bash
curl -X 'GET' \
  'http://localhost:4020/tasks/active' \ 
  -H 'accept: application/json'
```

### check task status
change `task_id` to the desired task id.

```bash
curl -X 'GET' \
  'http://localhost:4020/tasks/<task_id>' \
  -H 'accept: application/json'
```

### revoke (kill) a task

change `task_id` to the desired task id.

```bash
curl -X 'DELETE' \
  'http://localhost:4020/tasks/<task_id>' \
  -H 'accept: application/json'
```