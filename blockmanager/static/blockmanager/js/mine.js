function getCookie(name) {
	var cookieValue = null;
	if (document.cookie && document.cookie != ''){
		 var cookies = document.cookie.split(';');
		 for(var i = 0; i < cookies.length; i++){
			 var cookie = jQuery.trim(cookies[i]);
			 if(cookie.substring(0, name.length + 1) == (name + '=')){
				 cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				 break;
			 }
		}
	}
	return cookieValue;
}
$(function(){

	/*图标手风琴效果*/
	$(".icon-title").each(function(){

		$(this).click(function(){
			if($(this).next(".lct-icon").css("display")== "none")
			{
				$(this).next(".lct-icon").slideDown();
			}
			else
			{
				$(this).next(".lct-icon").slideUp();
			}
		});

	});
	/*图标手风琴效果*/

	//自适应高度
	var wheight = $(window).height()-43.5;
	$(".topo-left").css("height",wheight);
	$(".topo-right").css("height",wheight);

	//创建
	art("#new-btn").dialog({
		id: 'win1',
		title: '创建',
		content: $("#new-win").html(),
		follow: $('#new-btn'),
		resize:false,
		lock:true,
		button: [
			{
				name: '提交',
				callback: function () {
					$("#new-form").submit();
				},
				focus: true
			},
			{
				name: '关闭'
			}
		]
	});

	//导入
	art("#prop-btn").dialog({
		id: 'win2',
		title: '导入',
		content: $("#prop-win").html(),
		follow: $('#prop-btn'),
		resize:false,
		lock:true,
		button: [
			{
				name: '提交',
				callback: function () {
					$("#prop-form").submit();
				},
				focus: true
			},
			{
				name: '关闭'
			}
		]
	});
	
	$(".action-select").change(function(){

		var i = $(this).val();
		
		if(i == 1)//挂载
		{
			
			var listid_1 = $(this).next(".list-id").val();
			$("#gz-list-id").val(listid_1);
			art.dialog({
				id: 'win4',
				title: '挂载',
				content: $("#location-win").html(),
				lock:true,
				resize:false,
				button: [
					{
						name: '提交',
						callback: function () {
							$("#action-form").submit();
						},
						focus: true
					},
					{
						name: '关闭'
					}
				]
			});

		}
		else if(i == 2) //卸载
		{
			var listid_2 = $(this).next(".list-id").val();
			var csrftoken = getCookie('csrftoken');

			$.ajax({
				type: "POST",
				url: "umount/",
				data: {block_id:listid_2},
				cache:false,
				beforeSend:function(xhr, settings){
					 xhr.setRequestHeader("X-CSRFToken", csrftoken);
					if(!confirm("确认要卸载？"))
					{
						return false;
					}
				},
				success: function(data){
					//$("#eq-area").html(data);
					alert(data)
					window.location.reload(true)
				}
			});

		}

		else if(i == 3) //删除
		{
			var listid_3 = $(this).next(".list-id").val();
			var csrftoken = getCookie('csrftoken');

			$.ajax({
				type: "POST",
				url: "delete/",
				data: {block_id:listid_3},
				cache:false,
				beforeSend:function(xhr, settings){
					 xhr.setRequestHeader("X-CSRFToken", csrftoken);
					if(!confirm("确认要删除？"))
					{
						return false;
					}
				},
				success: function(data){
					//$("#eq-area").html(data);
					alert(data)
					window.location.reload(true)
					//history.go(0)
				}
			});

		}
	});

	//搜索挂载
	$("#gz-search").live("click",function(){

		var name = $("#gz-s-name").val();
		var ip = $("#gz-s-ip").val(); 

		$.ajax({
			type: "GET",
			url: "get_vms/",
			data: {the_name: name, the_ip: ip},
			cache:false,
			success: function(data){
				$("#vm-list").html(data['content']);
			}
		});

	});

});
