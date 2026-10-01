// 슬라이드 p4-v3-objinit-dup — 초기화자가 거절하는 대입, C# 3.0
using System;

class Item
{
    public readonly int Id;
    public string Name;
    string note;
    public string Note
    {
        get { return note; }
        private set { note = value; }
    }
}

class App
{
    static void Main()
    {
        Item a = new Item { Name = "a", Name = "b" };
        Item b = new Item { Id = 7 };
        Item c = new Item { Note = "x" };
        Console.WriteLine(a.Name + b.Id + c.Note);
    }
}
