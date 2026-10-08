// 슬라이드 p6-v5-rettypebad — 그 밖의 반환 형식은 거절, C# 5.0
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    static async int Number()
    {
        return await Task.FromResult(1);
    }

    static async IEnumerable<int> Numbers()
    {
        yield return await Task.FromResult(1);
    }

    static void Main() { }
}
