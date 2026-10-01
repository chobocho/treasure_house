// 슬라이드 p2-v1-mcreturn — 반환값은 마지막 것만, C# 1.0
using System;

delegate int Step(ref int total);

class App
{
    static int AddOne(ref int t) { t += 1; return 1; }
    static int Double(ref int t) { t *= 2; return 2; }
    static int AddTen(ref int t) { t += 10; return 3; }

    static void Main()
    {
        Step s = new Step(AddOne);
        s += new Step(Double);
        s += new Step(AddTen);

        int total = 5;
        int r = s(ref total);            // three calls, one result
        Console.WriteLine("returned: " + r);
        Console.WriteLine("total:    " + total);

        foreach (Step one in s.GetInvocationList())
        {
            int t = 0;
            Console.WriteLine(one.Method.Name + " -> " + one(ref t));
        }
    }
}
