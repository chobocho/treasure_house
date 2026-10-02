// 슬라이드 p10-v9-rec-ownprop — 같은 이름의 속성을 직접, C# 9.0
using System;

record Person(string FirstName, string LastName)
{
    protected string FirstName { get; init; } = FirstName;
    public string LastName { get; init; } = LastName.ToUpper();
}

#if BAD
record User(string Nick)
{
    public string Nick { get; init; } = "fixed";   // param unread
}
#endif

class App
{
    static void Main()
    {
        var p = new Person("Mads", "Torgersen");
        Console.WriteLine(p);                // FirstName is protected
        var (f, l) = p;                      // Deconstruct uses ours
        Console.WriteLine(f + " " + l);
    }
}
