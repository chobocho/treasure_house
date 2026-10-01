// 슬라이드 p4-v3-collinit-nested — 속성의 컬렉션에 더하기, C# 3.0
using System;
using System.Collections.Generic;

class Contact
{
    public string Name;
    List<string> phones = new List<string>();
    public List<string> Phones { get { return phones; } }   // no setter
}

class App
{
    static void Main()
    {
        List<Contact> contacts = new List<Contact>
        {
            new Contact { Name = "Chris",
                Phones = { "206-555-0101", "425-882-8080" } },
            new Contact { Name = "Bob", Phones = { "650-555-0199" } },
        };
        foreach (Contact c in contacts)
            Console.WriteLine(c.Name + ": "
                + string.Join(", ", c.Phones.ToArray()));
    }
}
