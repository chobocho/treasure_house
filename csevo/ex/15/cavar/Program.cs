// 슬라이드 p15-v14-ca-var — 변수일 때만 인스턴스 연산자, C# 14
using System;

struct Acc
{
    public int N;
#if !NOSTATIC
    public static Acc operator +(Acc a, int d)
    {
        Console.Write("[static +] ");
        return new Acc { N = a.N + d };
    }
#endif
    public void operator +=(int d)
    {
        Console.Write("[instance +=] ");
        N += d;
    }
}

class Holder
{
    public Acc Field;
    public Acc Prop { get; set; }
}

class Program
{
    static void Main()
    {
        var a = new Acc();
        var h = new Holder();
        var arr = new Acc[1];
        a += 1;            Console.WriteLine("local    " + a.N);
        h.Field += 1;      Console.WriteLine("field    " + h.Field.N);
        arr[0] += 1;       Console.WriteLine("element  " + arr[0].N);
        h.Prop += 1;       Console.WriteLine("property " + h.Prop.N);
        var r = a += 10;   Console.WriteLine("result   " + r.N + " "
                               + a.N);
    }
}
