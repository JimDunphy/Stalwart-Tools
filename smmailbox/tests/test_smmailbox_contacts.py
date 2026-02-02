import importlib.machinery
import importlib.util
import pathlib
import sys
import unittest


def load_smmailbox_module():
    smmailbox_path = pathlib.Path(__file__).resolve().parents[1] / "smmailbox"
    loader = importlib.machinery.SourceFileLoader("smmailbox", str(smmailbox_path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


SM = load_smmailbox_module()


class TestSmMailboxContacts(unittest.TestCase):
    def test_zimbra_date_to_partial_date(self) -> None:
        self.assertEqual(
            SM.zimbra_date_to_partial_date("2020-12-31"),
            {"@type": "PartialDate", "year": 2020, "month": 12, "day": 31},
        )
        self.assertEqual(
            SM.zimbra_date_to_partial_date("--12-31"),
            {"@type": "PartialDate", "month": 12, "day": 31},
        )
        self.assertIsNone(SM.zimbra_date_to_partial_date(""))
        self.assertIsNone(SM.zimbra_date_to_partial_date("2020-12"))
        self.assertIsNone(SM.zimbra_date_to_partial_date("not-a-date"))

    def test_contact_folder_name_mapping(self) -> None:
        self.assertEqual(
            SM.zimbra_contact_folder_to_address_book_name(
                SM.ZimbraContactFolder(folder_id="42", name="Friends", abs_folder_path="/Contacts/Friends")
            ),
            "Friends",
        )
        self.assertEqual(
            SM.zimbra_contact_folder_to_address_book_name(
                SM.ZimbraContactFolder(
                    folder_id="43", name="Friends", abs_folder_path="/Contacts/Work/Friends"
                )
            ),
            "Work/Friends",
        )
        self.assertEqual(
            SM.zimbra_contact_folder_to_address_book_name(
                SM.ZimbraContactFolder(
                    folder_id="13", name="Emailed Contacts", abs_folder_path="/Emailed Contacts"
                )
            ),
            "Emailed Contacts",
        )

    def test_is_zimbra_email_field(self) -> None:
        for value in ["email", "email2", "email3", "workEmail", "workEmail2"]:
            with self.subTest(value=value):
                self.assertTrue(SM.is_zimbra_email_field(value))
        for value in ["emailx", "email_", "workEmailx", "workEmail_"]:
            with self.subTest(value=value):
                self.assertFalse(SM.is_zimbra_email_field(value))

    def test_jscontact_name_fallbacks(self) -> None:
        self.assertEqual(
            SM.jscontact_name_from_attrs({"firstName": "Ada", "lastName": "Lovelace"})["full"],
            "Ada Lovelace",
        )
        self.assertEqual(
            SM.jscontact_name_from_attrs({"email": "user@example.com"})["full"],
            "user@example.com",
        )

    def test_jscontact_emails_contexts(self) -> None:
        emails = SM.jscontact_emails_from_attrs({"email": "a@example.com", "workEmail": "b@example.com"})
        assert emails is not None
        self.assertEqual(emails["email"]["contexts"], {"private": True})
        self.assertEqual(emails["workEmail"]["contexts"], {"work": True})

    def test_zimbra_get_contacts_parses_group_members(self) -> None:
        raw = b"""\
<Envelope>
  <Body>
    <GetContactsResponse xmlns="urn:zimbraMail">
      <cn id="19959" l="7">
        <a n="type">group</a>
        <a n="nickname">group_user</a>
        <m type="I" value="&quot;user&quot; &lt;user@example.com&gt;"/>
        <m t="I" v="user@example.com"/>
      </cn>
    </GetContactsResponse>
  </Body>
</Envelope>
"""
        orig = SM.http_post_xml
        SM.http_post_xml = lambda _url, _body, verify_tls: raw  # type: ignore[assignment]
        try:
            contacts = SM.zimbra_soap_get_contacts_by_ids(
                "https://example.test/service/soap",
                auth_token="token",
                ids=["19959"],
                verify_tls=True,
            )
        finally:
            SM.http_post_xml = orig  # type: ignore[assignment]

        self.assertEqual(len(contacts), 1)
        contact = contacts[0]
        self.assertEqual(contact.contact_id, "19959")
        self.assertEqual(contact.folder_id, "7")
        self.assertEqual(contact.attrs.get("nickname"), "group_user")
        self.assertEqual(
            [m.value for m in contact.members],
            ['"user" <user@example.com>', "user@example.com"],
        )

    def test_jmap_card_from_zimbra_contact_group(self) -> None:
        contact = SM.ZimbraContact(
            contact_id="19959",
            folder_id="7",
            attrs={"type": "group", "nickname": "group_user"},
            members=(
                SM.ZimbraContactGroupMember(member_type="I", value='"user" <user@example.com>'),
                SM.ZimbraContactGroupMember(member_type="I", value="user@example.com"),
            ),
        )
        card = SM.jmap_card_from_zimbra_contact(contact, address_book_id="ab1", stable_uid="uid1")
        self.assertEqual(card["uid"], "uid1")
        self.assertEqual(card["addressBookIds"], {"ab1": True})
        self.assertEqual(card.get("kind"), "group")
        self.assertEqual(card.get("members"), {'"user" <user@example.com>': True, "user@example.com": True})


if __name__ == "__main__":
    unittest.main()
