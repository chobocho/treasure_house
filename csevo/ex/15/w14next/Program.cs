// 슬라이드 p15-sum-next — C# 15 의 꼴을 이 컴파일러에, C# 14
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
#if WITH
        List<int> a = [with(capacity: 8), 1, 2];    // collection args
#endif
#if LABEL
        outer: for (int i = 0; i < 3; i++)
            for (int j = 0; j < 3; j++)
                if (j == 1) continue outer;          // labeled continue
#endif
        Console.WriteLine("compiled");
    }
}
#if UNION
record Cat(string Name);
record Dog(string Name);
union Pet(Cat, Dog);
#endif
