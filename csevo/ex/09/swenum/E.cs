// 슬라이드 p9-v8-switchexpr-enum — 이름 없는 열거 값, C# 8.0
using System;
using System.Runtime.CompilerServices;

enum B { Off, On }

class App
{   // every named member is covered, still a warning: (B)2
    static string Name(B c) => c switch
    {
        B.Off => "off",
        B.On => "on",
    };

    static void Main()
    {
        Console.WriteLine(Name(B.On));
        try
        {
            Console.WriteLine(Name((B)7));
        }
        catch (SwitchExpressionException e)
        {
            Type t = e.GetType();
            Console.WriteLine(t.FullName);
            Console.WriteLine("base: " + t.BaseType.FullName);
            Console.WriteLine("UnmatchedValue: " + e.UnmatchedValue);
            Console.WriteLine("assembly: " + t.Assembly.GetName().Name);
        }
    }
}
