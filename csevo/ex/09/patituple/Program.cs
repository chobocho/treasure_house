// 슬라이드 p9-v8-pospat-ituple — object 와 ITuple, C# 8.0
using System;
using System.Runtime.CompilerServices;

class Pair : ITuple                    // no Deconstruct at all
{
    public int Length => 2;
    public object this[int i] => i == 0 ? (object)"left" : 42;
}

class App
{
    static string Test(object o) => o switch
    {
        (int a, int b) => "two ints " + (a + b),
        (string s, 42) => "string and 42: " + s,
        (_, _, _) => "three of anything",
        _ => "no match: " + (o == null ? "null" : o.GetType().Name),
    };

    static void Main()
    {
        Console.WriteLine(Test(Tuple.Create(1, 2)));        // class
        Console.WriteLine(Test((3, 4)));                    // boxed
        Console.WriteLine(Test(new Pair()));
        Console.WriteLine(Test(("x", 1.0, 'c')));
        Console.WriteLine(Test(new[] { 1, 2 }));
        Console.WriteLine(Test(null));
    }
}
