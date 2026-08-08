"""招かれている人の名簿を、利用者プールで実現する。

この名簿はこの文脈の外にある仕組みで、合言葉の扱いもそちらが持つ。
ここはその仕組みを、application が言う語（探す・招く・外す・送り直す）へ
翻訳するだけに徹する。
"""
from __future__ import annotations


class CognitoPublisherDirectory:
    """招かれている人の名簿を、利用者プールの上で扱う。"""
    def __init__(self, user_pool_id: str, admin_group: str):
        import boto3

        self._pool = user_pool_id
        self._admin_group = admin_group
        self._idp = boto3.client("cognito-idp")

    """招かれている人の名簿。実体は利用者プール。"""

    def find(self, publisher_id):
        """その人が名簿に載っているかを調べる。

        Args:
            publisher_id: 探す人の識別子。

        Returns:
            載っていればその人の記録。載っていなければ None。

        Raises:
            なし。
        """
        try:
            got = self._idp.admin_get_user(UserPoolId=self._pool, Username=publisher_id)
        except Exception:
            return None
        # 仮の合言葉のまま入っていない人は、まだ招待に応じていない
        got["status"] = ("invited" if got.get("UserStatus") == "FORCE_CHANGE_PASSWORD"
                         else "active")
        return got

    def invite(self, email):
        """招いて、名簿が持つ識別子を返す。

        宛先で入る設定にしてあるため、名簿の識別子は宛先そのものではない。
        公開したものの持ち主はこの識別子で記録されるので、宛先を返すと
        招いた直後に引き継ぎ先として指せなくなる。
        """
        try:
            created = self._idp.admin_create_user(
                UserPoolId=self._pool, Username=email,
                UserAttributes=[{"Name": "email", "Value": email},
                                {"Name": "email_verified", "Value": "true"}],
                DesiredDeliveryMediums=["EMAIL"])
            return created["User"]["Username"]
        except self._idp.exceptions.UsernameExistsException:
            # 既に招かれている。合言葉も公開したものも変えない
            return self._idp.admin_get_user(UserPoolId=self._pool, Username=email)["Username"]

    def remove(self, publisher_id):
        """その人を名簿から外す。

        Args:
            publisher_id: 外す人の識別子。

        Returns:
            なし。

        Raises:
            なし。
        """
        self._idp.admin_delete_user(UserPoolId=self._pool, Username=publisher_id)

    def list(self):
        """名簿に載っている人を並べる。

        Returns:
            招かれている人の一覧。

        Raises:
            なし。
        """
        people, token = [], None
        while True:
            kw = {"UserPoolId": self._pool, "Limit": 60}
            if token:
                kw["PaginationToken"] = token
            res = self._idp.list_users(**kw)
            for u in res.get("Users", []):
                attrs = {a["Name"]: a["Value"] for a in u.get("Attributes", [])}
                people.append({
                    "id": u["Username"],
                    "email": attrs.get("email", ""),
                    # 仮の合言葉のまま入っていない人は、まだ招待に応じていない
                    "status": ("invited" if u.get("UserStatus") == "FORCE_CHANGE_PASSWORD"
                               else "active"),
                })
            token = res.get("PaginationToken")
            if not token:
                return people

    def resend(self, publisher_id):
        """招きの案内をもう一度送る。

        Args:
            publisher_id: 送り直す相手の識別子。

        Returns:
            なし。

        Raises:
            なし。
        """
        person = self.find(publisher_id) or {}
        email = {a["Name"]: a["Value"]
                 for a in person.get("UserAttributes", [])}.get("email", publisher_id)
        self._idp.admin_create_user(
            UserPoolId=self._pool, Username=publisher_id,
            UserAttributes=[{"Name": "email", "Value": email},
                            {"Name": "email_verified", "Value": "true"}],
            MessageAction="RESEND",
            DesiredDeliveryMediums=["EMAIL"])

    def admins(self):
        """名簿を管理してよい人を並べる。

        Returns:
            管理してよい人の一覧。

        Raises:
            なし。
        """
        res = self._idp.list_users_in_group(UserPoolId=self._pool,
                                      GroupName=self._admin_group, Limit=60)
        return {u["Username"] for u in res.get("Users", [])}
