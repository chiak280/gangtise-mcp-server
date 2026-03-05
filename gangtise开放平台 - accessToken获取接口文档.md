# gangtise开放平台 - accessToken获取接口文档

## 1. 接口基本信息

|项|内容|
|---|---|
|接口名称|获取accessToken（鉴权令牌）|
|接口描述|用于获取调用平台所有接口所需的accessToken，V2版本返回的token已携带Bearer前缀，无需额外拼接|
|请求URL|[https://open.gangtise.com/application/auth/oauth/open/loginV2](https://open.gangtise.com/application/auth/oauth/open/loginV2)|
|请求方式|POST|
## 2. 请求参数说明

|参数名|必选|类型|说明|
|---|---|---|---|
|accessKey|是|String|开发账号的AK（Access Key）|
|secretAccessKey|是|String|开发账号的SK（Secret Access Key）|
## 3. 请求示例

```JSON
{
    "accessKey":"accessKey",
    "secretAccessKey":"secretAccessKey"
}
```

## 4. 返回示例

```JSON
{
    "code": "000000",
    "msg": "请求成功",
    "status": true,
    "data": {
        "accessToken": "Bearer 3d08a305-ae17-4540-b5ee-976a50219287",
        "expiresIn": 14400,
        "userId": "1273742407104651264",
        "uid": 290,
        "userName": "一号开发者",
        "ipaddr": "172.20.122.64",
        "tenantId": 183,
        "time": 1679031461
    }
}
```

## 5. 返回参数说明

|参数名|类型|说明|
|---|---|---|
|accessToken|String|开发账号token，已携带Bearer前缀，可直接用于接口请求头|
|expiresIn|Long|token有效时间（单位：秒）|
|uid|Integer|开发账号的uid|
|userName|String|开发账号名称|
|tenantId|Integer|开发账号所属租户Id|
|time|Integer|开发账号登录时间（时间戳，单位：秒）|
|userId|String|账号唯一标识（扩展字段）|
|ipaddr|String|登录IP地址（扩展字段）|
## 6. 调用示例（Java）

```Java
String ak = "你的accessKey";
String sk = "你的secretAccessKey";
LoginInfo loginInfo = new LoginInfo(ak,sk);

AccessToken accessToken = LoginClient.getToken(loginInfo);
System.out.println(accessToken.getAccess_token());
```

## 7. 备注

- 该接口是调用平台所有其他接口的**前置步骤**，必须先获取有效的accessToken；

- V2版本返回的accessToken已包含`Bearer `前缀，无需手动拼接，可直接放入Authorization请求头；

- 更多返回错误代码请查看平台首页的错误代码描述。

---

### 补充整合说明

若需要将此接口整合到之前的完整开发文档指南中，可将其放在「2. 接入前置通用规范」后作为**2.3 鉴权接口（必调）** 章节，成为所有接口调用的前置基础步骤。

---

## 8. 统一返回说明

### 8.1 统一返回格式

```JSON
{
    "code": "000000",
    "msg": "请求成功",
    "status": true,
    "data": ""
}
```

### 8.2 统一返回参数说明

|参数名|类型|说明|
|---|---|---|
|code|String|返回错误编码。 000000代表正常返回，其余代表异常|
|msg|String|请求返回提示信息|
|status|Boolean|请求处理结果，true：正常 false：异常|
|data|Object|接口返回数据|
### 8.3 HTTP状态码说明

|状态码|说明|
|---|---|
|200|请求成功|
|400|参数错误|
|403|未开通接口权限|
|404|接口不存在|
|429|接口繁忙或接口调用次数受限|
|500|内部错误|
### 8.4 错误码说明

|错误编码|说明|
|---|---|
|999999|系统错误|
|999997|未开通接口权限|
|999995|积分不足|
|900002|uid为空|
|900001|请求参数为空|
|8000014|开发账号AK错误|
|8000015|开发账号SK错误|
|8000016|开发账号状态异常|
|903301|今日调用次数已达到上限|
> （注：文档部分内容可能由 AI 生成）