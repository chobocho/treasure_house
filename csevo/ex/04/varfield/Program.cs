// 슬라이드 p4-v3-var-field — var 는 지역 변수에만, C# 3.0
using System;

class Counter
{
    var count = 0;                      // field
    public var Next() { return ++count; }  // return type
    public void Add(var n) { }            // parameter
}

class App
{
    static void Main()
    {
        Console.WriteLine(new Counter().Next());
    }
}
