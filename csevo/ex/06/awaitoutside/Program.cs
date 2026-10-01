// 슬라이드 p6-v5-awaitname — async 밖의 await, C# 5.0
using System.Threading.Tasks;

class App
{
    static int NotAsync()
    {
        return await Task.FromResult(1);
    }

    static void Main() { }
}
