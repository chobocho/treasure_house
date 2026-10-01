// 슬라이드 p2-v1-boxmutfail — 언박싱 결과에는 대입할 수 없다, C# 1.0
using System;
using System.Collections;

struct Counter { public int N; }

class App
{
    static void Main()
    {
        ArrayList list = new ArrayList();
        list.Add(new Counter());
        ((Counter)list[0]).N = 5;
        Console.WriteLine(((Counter)list[0]).N);
    }
}
