// 슬라이드 p2-v1-flags — [Flags] 와 비트 조합, C# 1.0
using System;

[Flags]
enum Perm { None = 0, Read = 1, Write = 2, Exec = 4 }

enum Plain { None = 0, Read = 1, Write = 2, Exec = 4 }

class App
{
    static void Main()
    {
        Perm p = Perm.Read | Perm.Write;
        Console.WriteLine(p);
        Console.WriteLine(Plain.Read | Plain.Write);
        Console.WriteLine((p & Perm.Write) != 0);
        Console.WriteLine((p & Perm.Exec) == Perm.Exec);

        Perm q = (Perm)Enum.Parse(typeof(Perm), "Read, Exec");
        Console.WriteLine((int)q);
        Console.WriteLine((Perm)8);
        Console.WriteLine((Perm)9);
        Console.WriteLine(Perm.None);
    }
}
