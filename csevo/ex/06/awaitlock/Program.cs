// 슬라이드 p6-v5-awaitlock — lock 안의 await, C# 5.0
using System.Threading.Tasks;

class App
{
    static readonly object gate = new object();
    static int count;

    static async Task Add()
    {
        lock (gate)
        {
            await Task.Delay(1);        // may resume on another thread
            count++;
        }
    }

    static void Main() { Add().Wait(); }
}
