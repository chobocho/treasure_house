// 슬라이드 p2-v1-opcomp14 — 복합 대입 연산자 직접 정의는 C# 14, C# 1.0
using System;

class Total
{
    public int Sum;
    public Total(int s) { Sum = s; }

    public void operator +=(int n)            // C# 14: in place
    {
        Console.WriteLine("  op_AdditionAssignment(" + n + ")");
        Sum += n;
    }
}

class App
{
    static void Main()
    {
        Total t = new Total(1);
        Total alias = t;
        t += 2;
        Console.WriteLine("t.Sum=" + t.Sum + " alias.Sum=" + alias.Sum);
    }
}
