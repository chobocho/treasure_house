// 슬라이드 p2-v1-delegate — 대리자 선언과 생성, C# 1.0
using System;

delegate int Op(int a, int b);

class Calc
{
    int bias;
    public Calc(int bias) { this.bias = bias; }
    public int AddBias(int a, int b) { return a + b + bias; }
}

class App
{
    static int Add(int a, int b) { return a + b; }
    static int Mul(int a, int b) { return a * b; }

    static int Apply(Op op, int a, int b) { return op(a, b); }

    static void Main()
    {
        Op add = new Op(Add);                   // C# 1: always 'new'
        Op mul = new Op(Mul);
        Op biased = new Op(new Calc(100).AddBias);
        Console.WriteLine(Apply(add, 6, 7) + " " + Apply(mul, 6, 7)
            + " " + Apply(biased, 6, 7));
        Console.WriteLine("Invoke: " + add.Invoke(1, 2));
        Console.WriteLine("Method: " + add.Method.Name
            + ", Target null: " + (add.Target == null));
        Console.WriteLine("Method: " + biased.Method.Name
            + ", Target: " + biased.Target.GetType().Name);
    }
}
