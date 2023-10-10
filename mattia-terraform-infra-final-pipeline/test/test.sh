
for i in $(seq 99); do
    curl -X POST http://localhost:8080/view/Thesis%20Pipelines/job/Pipeline%20IaC%20and%20IaCSec/build?delay=0sec --data verbosity=high --user Matt2212:118ac65a7b184f21395807e323fd5030aa
    echo "execution $i"
    sleep 40
done