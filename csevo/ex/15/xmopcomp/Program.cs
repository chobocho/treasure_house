// 슬라이드 p15-v14-xm-op-compound — 확장 복합 대입 연산자, C# 14
using System;
using System.Collections.Generic;
using System.Text;

struct Meter { public int Value; }

static class Ops
{
    extension(List<int> list)              // reference type: by value
    {
        public void operator +=(int n) => list.Add(n);
    }

    extension(ref Meter m)                 // value type: by ref
    {
        public void operator +=(int n) => m.Value += n;
    }

    extension(StringBuilder sb)
    {
        public void operator +=(string s) => sb.Append(s);
    }
#if VALUE
    extension(Meter m)                     // value type without ref
    {
        public void operator -=(int n) => m.Value -= n;
    }
#endif
}

class Program
{
    static void Main()
    {
        var list = new List<int>();
        List<int> same = list;
        list += 1;
        list += 2;                         // mutates in place
        Console.WriteLine(list.Count + " "
            + ReferenceEquals(list, same));
        var m = new Meter();
        m += 5;
        Console.WriteLine(m.Value);
#if SB
        var sb = new StringBuilder("a");
        sb += "b";                         // object + string wins
#endif
    }
}
