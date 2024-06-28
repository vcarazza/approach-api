# externalLPValorAPI
External API to provide informations about officers (name, email) to landing page Valor Investimentos


sam build --use-container; if ($?) { sam package --output-template-file packaged.yml --s3-bucket approach --s3-prefix api-approach; if ($?) { sam deploy --template-file packaged.yml --stack-name intranet-api-approach --capabilities CAPABILITY_IAM --s3-bucket approach --s3-prefix api-approach } }

sam build --use-container --profile 'vitor_pessoal'
if ($?) { 
    sam package --output-template-file packaged.yml --s3-bucket approach --s3-prefix api-approach --profile 'vitor_pessoal'
    if ($?) { 
        sam deploy --template-file packaged.yml --stack-name intranet-api-approach --capabilities CAPABILITY_IAM --s3-bucket approach --s3-prefix api-approach --profile 'vitor_pessoal'
    }
}
