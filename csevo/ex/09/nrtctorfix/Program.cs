// 슬라이드 p9-v8-nrt-ctorfix — CS8618 을 푸는 네 길, C# 8.0
#nullable enable
using System;

class Person
{
    public string A = "";                  // 1. an initializer
    public string B;                       // 2. set in every ctor
    public string? C { get; set; }         // 3. admit it can be null
    public string D = null!;               // 4. "set later, trust me"

    public Person() { B = "b"; }
    public Person(string b) { B = b; }

    public void Init() { D = "d"; }
}

class App
{
    static void Main()
    {
        var p = new Person();
        Console.WriteLine("[" + p.A + "] " + p.B + " "
            + (p.C ?? "null"));
        p.Init();
        Console.WriteLine(p.D.Length);
    }
}
