// 슬라이드 p12-v11-file — file 형식(Program.cs), C# 11
using System;

class Widget                     // an ordinary internal type
{
    public static string Who => "Widget of Program.cs";
}

class Program
{
    static void Main()
    {
        Console.WriteLine(A.Run());
        Console.WriteLine(B.Run());
        Console.WriteLine(Widget.Who);
    }
}
