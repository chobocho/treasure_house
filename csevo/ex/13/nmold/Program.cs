// 슬라이드 p13-v12-nm-old — C# 6 에도 되던 길, C# 6
using System;

class Person
{
    public string Name = "";

    public static string Qualified()
    {
        // through the type name: accepted since C# 6
        return nameof(Person.Name.Length);
    }
#if BAD
    public static string Simple()
    {
        return nameof(Name.Length);   // simple name: C# 12
    }
#endif
}

class App
{
    static void Main()
    {
        Console.WriteLine(Person.Qualified());
    }
}
