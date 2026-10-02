// 슬라이드 p7-v6-nameof-ident — nameof 라는 메서드가 있으면, C# 6.0
using System;

class Old
{
    // C# 5 code could already have a method called nameof
    static string nameof(object o) { return "method: " + o; }

    public static void Run()
    {
        int x = 42;
        Console.WriteLine(nameof(x));          // calls the method
    }
}

class New
{
    public static void Run()
    {
        int x = 42;
        Console.WriteLine(nameof(x));          // the operator
        Console.WriteLine(x);
    }
}

class App
{
    static void Main()
    {
        Old.Run();
        New.Run();
    }
}
