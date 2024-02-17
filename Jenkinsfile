@Library('emo-shared-lib') _
pipeline {
  parameters {
    gitParameter(branchFilter: 'origin/(.*)',
      defaultValue: 'main',
      selectedValue: 'DEFAULT',
      name: 'Branch',
      type: 'PT_BRANCH',
      description: 'Git branch name to checkout. Default is main')

    choice(name: 'Universe',
      choices: ['ci', 'cert', 'anon', 'uat', 'bazaar'],
      description: 'Choose proper universe to deploy')

    password(name: 'ApiKey', description: 'Value of apikey secret')
    password(name: 'AccessToken', description: 'Value of Lacework AccessToken secret')
    password(name: 'DatadogKey', description: 'Value of Datadog API Key secret')
  }
  agent {
    ecs {
      inheritFrom labelDiscovery.getPythonLabelByUniverse("${params.Universe}")
      taskrole "arn:aws:iam::${labelDiscovery.getAccountIdByUniverse(params.Universe)}:role/nexus/jenkins/job/EmodbBuild"
    }
  }
  options {
    timeout(time: 10, unit: 'MINUTES')
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timestamps()
    ansiColor('xterm')
  }
  environment {
    EnvironmentTag = labelDiscovery.getVpcByUniverse("${params.Universe}")
    StackName = "${Universe}-emoji-secret"
    Region = "us-east-1"
    Team = "emodb-dev@bazaarvoice.com"
    Service = "emoji"
    Datatype = "client+personal"
  }
  stages {
    stage('Deploy secrets') {
      steps {
        dir("ops/cfn") {
          sh '''
            aws cloudformation deploy          \
              --stack-name ${StackName}        \
              --template-file secrets.cfn.yml  \
              --region ${Region}               \
              --capabilities CAPABILITY_IAM    \
              --no-fail-on-empty-changeset     \
              --parameter-overrides            \
                Universe=${Universe}           \
                AccessToken=${AccessToken}     \
                DatadogKey=${DatadogKey}       \
                ApiKey=${ApiKey}               \
              --tags                           \
                bv:nexus:team=${Team}          \
                bv:nexus:vpc=${EnvironmentTag} \
                bv:system=emodb                \
                bv:nexus:service=${Service}    \
                bv:nexus:owner=${Team}         \
                bv:nexus:costcenter=${Team}    \
                bv:nexus:datatype=${Datatype}  \
                bv:nexus:env=${EnvironmentTag}
          '''
        }
      }
    }
  }
  post {
    success {
      script {
        notifyBuild.notifyToSlack('SUCCESS')
      }
    }
    failure {
      script {
        notifyBuild.notifyToSlack('FAILED')
      }
    }
  }
}
