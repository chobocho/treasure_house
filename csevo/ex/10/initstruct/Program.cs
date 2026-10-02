// 슬라이드 p10-v9-init-struct — readonly struct 와 init, C# 9.0
using System;

readonly struct ReadonlyStruct1
{
    public int Prop1 { get; init; }          // allowed
}

struct ReadonlyStruct2
{
    public readonly int Prop2 { get; init; } // allowed
#if BAD
    public int Prop3 { get; readonly init; } // error
#endif
}

class App
{
    static void Main()
    {
        var a = new ReadonlyStruct1 { Prop1 = 1 };
        var b = new ReadonlyStruct2 { Prop2 = 2 };
        Console.WriteLine(a.Prop1 + b.Prop2);
    }
}
