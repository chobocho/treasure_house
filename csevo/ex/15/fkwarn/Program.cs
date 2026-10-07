// 슬라이드 p15-v14-fk-warn — 뒷받침 필드와 필드 경고, C# 14
using System;

class C
{
    int x;                                     // never assigned
    int y;                                     // never read
    int A { get => 0; set => field = value; }  // field never read
    int B => field;                            // field never assigned
    int D { set => field = value; }            // set only: allowed
#if SETONLY
    int F { set; }
#endif

    public void Run()
    {
        y = 1; A = 2; D = 3;
        Console.WriteLine(x + A + B);
    }
}

class Program
{
    static void Main() => new C().Run();
}
