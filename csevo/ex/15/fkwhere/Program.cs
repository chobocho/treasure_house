// 슬라이드 p15-v14-fk-where — field 가 키워드인 자리, C# 14
using System;
using System.Collections.Generic;

class C
{
    const int field = -1;                  // a member named 'field'
    readonly int[] data = { 10, 20 };

    public int Init { get; } = field;      // initializer: the const
    public int Prop => @field;             // escaped: the const
    public int this[int i] => field + data[i];  // indexer: identifier
    public int Method() => field;          // method: identifier

    public event Action E
    {
        add { Console.WriteLine("add " + field); }  // event: identifier
        remove { }
    }
#if NAMEOF
    public string Name => nameof(field);
#endif
#if LAMBDA
    public bool Any => new List<int>().Exists(field => field > 0);
#endif
}

class Program
{
    static void Main()
    {
        var c = new C();
        Console.WriteLine(c.Init + " " + c.Prop + " " + c[0]
            + " " + c.Method());
        c.E += () => { };
    }
}
