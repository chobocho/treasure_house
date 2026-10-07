// 슬라이드 p16-ld-rungs — 버전마다 게이트 하나씩, C# 1–14
using System;
#if R1
[module: System.Security.UnverifiableCode]
#endif
#if R10
namespace Ladder;
#endif
delegate int F(int x);
class Program
{
    static object seen;
    static void Use(object o) { seen = o; }
#if R7_2
    private protected int pp = 1;
#endif
#if R5
    static async System.Threading.Tasks.Task Wait()
    {
        await System.Threading.Tasks.Task.Yield();
    }
#endif
#if R14
    Program next;
#endif
    static void Main()
    {
#if R2
        Use(new System.Collections.Generic.List<int>());
#endif
#if R3
        F f = x => x; Use(f);
#endif
#if R4
        Use(o: 1);
#endif
#if R6
        Use($"{seen}");
#endif
#if R7
        Use((1, 2));
#endif
#if R7_1
        int d = default; Use(d);
#endif
#if R7_3
        Use((1, 2) == (1, 2));
#endif
#if R8
        seen ??= "x";
#endif
#if R9
        Program q = new(); Use(q);
#endif
#if R11
        Use("""raw""");
#endif
#if R12
        int[] a = [1, 2]; Use(a);
#endif
#if R13
        lock (new System.Threading.Lock()) { }
#endif
#if R14
        Program p = null; p?.next = p;
#endif
        Console.WriteLine("ok " + (seen == null));
    }
}
