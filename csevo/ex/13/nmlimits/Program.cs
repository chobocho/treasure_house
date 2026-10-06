// 슬라이드 p13-v12-nm-limits — C# 12 에서도 안 되는 nameof, C# 12.0
using System;

class Person
{
    public string Name = "";
    public string[] Tags = { };

    public static string Ok() => nameof(Tags.Length);
#if BAD
    public static string A() => nameof(Name.Length.ToString());
#elif BAD2
    public static string B() => nameof(this.Name);
#elif BAD3
    public static string C() => nameof(Tags[0].Length);
#endif
}

class App
{
    static void Main()
    {
        Console.WriteLine(Person.Ok());
    }
}
