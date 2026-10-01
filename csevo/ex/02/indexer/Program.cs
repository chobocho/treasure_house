// 슬라이드 p2-v1-indexer — 인덱서와 그 오버로드, C# 1.0
using System;
using System.Collections;

class Phonebook
{
    ArrayList names = new ArrayList();
    ArrayList numbers = new ArrayList();

    public void Add(string name, string number)
    {
        names.Add(name);
        numbers.Add(number);
    }

    public string this[int i]                  // by position
    {
        get { return (string)names[i]; }
    }

    public string this[string name]            // by key
    {
        get
        {
            int i = names.IndexOf(name);
            return i < 0 ? "(none)" : (string)numbers[i];
        }
        set { Add(name, value); }
    }
}

class App
{
    static void Main()
    {
        Phonebook book = new Phonebook();
        book.Add("kim", "010-1111");
        book["lee"] = "010-2222";
        Console.WriteLine(book[1] + " -> " + book["lee"]);
        Console.WriteLine("park -> " + book["park"]);
    }
}
