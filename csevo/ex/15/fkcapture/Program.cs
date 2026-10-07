// 슬라이드 p15-v14-fk-capture — 람다·지역 함수 안의 field, C# 14
using System;
using System.Collections.Generic;

class C
{
    public static int Ticks
    {
        get
        {
            Func<int> next = static () => ++field;   // static field
            next();
            return next();
        }
    }
    public string Log
    {
        get
        {
            void Add(string s) => field = field + s;  // captures this
            Add("a");
            Add("b");
            return field;
        }
    }
#if NAMEOF
    public string Name => nameof(field);
#endif
#if LAMBDA
    public bool Any => new List<int>().Exists(field => field > 0);
#endif
#if STATIC
    public int Bad => ((Func<int>)(static () => field))();
#endif
}

class Program
{
    static void Main()
    {
        Console.WriteLine(C.Ticks + " " + C.Ticks);
        var c = new C();
        Console.WriteLine(c.Log + " " + c.Log);
    }
}
