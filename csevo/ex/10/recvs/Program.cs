// 슬라이드 p10-v9-rec-vs — class·struct·record·튜플을 나란히, C# 9.0
using System;

class PC { public int X; public PC(int x) { X = x; } }
struct PS { public int X; public PS(int x) { X = x; } }
record PR(int X);

class App
{
    static void Row(string kind, object a, object b, string eqOp)
    {
        Console.WriteLine("{0,-7} {1,-6} {2,-6} {3}", kind, eqOp,
            a.Equals(b), a);
    }

    static void Main()
    {
        Console.WriteLine("kind    ==     Equals ToString");
        PC c1 = new PC(1), c2 = new PC(1);
        Row("class", c1, c2, (c1 == c2).ToString());
        PS s1 = new PS(1), s2 = new PS(1);
        Row("struct", s1, s2, "-");          // no == unless declared
#if BAD
        bool same = s1 == s2;
#endif
        PR r1 = new PR(1), r2 = new PR(1);
        Row("record", r1, r2, (r1 == r2).ToString());
        var t1 = (X: 1, Y: 2);
        var t2 = (X: 1, Y: 2);
        Row("tuple", t1, t2, (t1 == t2).ToString());  // C# 7.3
    }
}
