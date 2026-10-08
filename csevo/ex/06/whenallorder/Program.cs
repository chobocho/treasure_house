// 슬라이드 p6-v5-whenallorder — WhenAll 의 결과는 인수 차례, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static void Main()
    {
        var a = new TaskCompletionSource<string>();
        var b = new TaskCompletionSource<string>();
        var c = new TaskCompletionSource<string>();
        Task<string[]> all = Task.WhenAll(a.Task, b.Task, c.Task);

        c.SetResult("c");               // finish in reverse order
        b.SetResult("b");
        Console.WriteLine("two of three: " + all.Status);
        a.SetResult("a");
        Console.WriteLine("result: " + string.Join(",", all.Result));

        Task<int[]> none = Task.WhenAll(new Task<int>[0]);
        Console.WriteLine("no tasks: " + none.Status
            + ", length " + none.Result.Length);
    }
}
