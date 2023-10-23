
for i in $(seq 99); do
    curl -I http://admin:e17a935058ef4a6ca1cd07aec9a0de45@localhost:8080/job/thesis/buildWithParameters?token=super_secret_token
    echo "execution $i"
    sleep 40
done