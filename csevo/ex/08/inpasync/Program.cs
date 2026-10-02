// 슬라이드 p8-v7_2-in-limit — async 메서드의 in 매개변수, C# 7.2
using System.Threading.Tasks;

class App
{
    static async Task<int> Later(in int x)
    {
        await Task.Yield();             // an async method
        return x;
    }

    static void Main() { }
}
