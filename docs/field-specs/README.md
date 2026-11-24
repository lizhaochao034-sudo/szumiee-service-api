# 卓工平台字段表

本目录收录 10 份业务字段表与 2 份共享定义。两个后端仓库使用同一套定义。

文件取自项目成员下载的字段表，并逐份核对为[源仓库提交 1a5eecf](https://github.com/0888269/szumiee-web-v1/tree/1a5eecf862f348233b80557b951801c8534c6779/backend-schema) 中的对应文件。

## 业务字段表

- [Account.json](./Account.json)
- [assignment.json](./assignment.json)
- [course.json](./course.json)
- [route.json](./route.json)
- [adminAccount.json](./adminAccount.json)
- [badge.json](./badge.json)
- [certification.json](./certification.json)
- [message.json](./message.json)
- [plan.json](./plan.json)
- [todo.json](./todo.json)

## 共享定义

- [课程共享定义](./共享定义字段/course_shared.json)由[课程表](./course.json)引用。课程字段在共享定义中维护。
- [作业共享定义](./共享定义字段/assignment_shared.json)由[作业表](./assignment.json)引用。作业表另定义学员提交实例和流转记录。

同步时请保留文件名大小写及共享定义的相对引用。跨仓库更新时使用同一来源版本。
