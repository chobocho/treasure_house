// 슬라이드 p2-v1-delbegin — .NET 10 의 BeginInvoke, C# 1.0
using System;

delegate int Op(int a, int b);

class App
{
    static int Add(int a, int b) { return a + b; }

    static void Main()
    {
        Op op = new Op(Add);
        try
        {
            IAsyncResult r = op.BeginInvoke(1, 2, null, null);
            Console.WriteLine("result: " + op.EndInvoke(r));
        }
        catch (PlatformNotSupportedException e)
        {
            Console.WriteLine(e.GetType().Name);
            Console.WriteLine(e.Message);
        }
    }
}
